"""
Payment Routes
==============
POST /api/payment/create-order   - Create Razorpay order (requires auth)
POST /api/payment/verify         - Verify payment after checkout completes
POST /api/payment/webhook        - Razorpay webhook (server-to-server)
GET  /api/payment/status         - Check account or search-specific payment status
"""

import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import razorpay
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database import crud
from database.connection import get_db
from utils.auth_utils import decode_token

router = APIRouter()

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", RAZORPAY_KEY_SECRET)
AUDIT_PRICE_INR = int(os.getenv("AUDIT_PRICE_INR", "2000"))
AUDIT_PRICE_PAISE = AUDIT_PRICE_INR * 100
PORTAL_ACCESS_DAYS = int(os.getenv("PORTAL_ACCESS_DAYS", "90"))


def _razorpay_client():
    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        raise HTTPException(500, "Razorpay not configured. Add keys to .env")
    return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


def _get_current_email(request: Request) -> Optional[str]:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    payload = decode_token(auth[7:])
    return payload.get("sub") if payload else None


async def _sync_client_with_selected_search(db: AsyncSession, client_obj, search):
    if not search:
        return

    if search.legacy_lead_id and client_obj.lead_id != search.legacy_lead_id:
        client_obj.lead_id = search.legacy_lead_id
        matched_lead = await crud.get_lead_by_id(db, search.legacy_lead_id)
        if matched_lead and matched_lead.status == "new":
            matched_lead.status = "stage4_paid"


async def _resolve_payment_client_for_search(
    db: AsyncSession,
    account_client,
    search,
    plan_type: str,
):
    if search:
        existing_job = await crud.get_latest_audit_job_for_search(db, search.id)
        if existing_job:
            raise HTTPException(400, "A detailed audit has already been started for this saved search.")

    if account_client.paid_at is None:
        return account_client

    return await crud.create_shadow_audit_client(
        db,
        account_email=account_client.email,
        password_hash=account_client.password_hash,
        lead_id=search.legacy_lead_id if search else account_client.lead_id,
        plan_type=plan_type,
        search_id=search.id if search else None,
    )


async def _upsert_payment_success(
    db: AsyncSession,
    *,
    payment_client,
    user,
    order_record,
    email: str,
    payment_id: str,
    amount_paid: float,
    currency: str,
):
    now = datetime.now(timezone.utc)
    payment_client.payment_id = payment_id
    payment_client.order_id = order_record.razorpay_order_id
    payment_client.amount_paid = amount_paid
    payment_client.currency = currency
    payment_client.paid_at = now
    payment_client.plan_type = "basic_audit"
    payment_client.audit_status = "pending"
    payment_client.access_expires_at = now + timedelta(days=PORTAL_ACCESS_DAYS)

    if not payment_client.lead_id:
        matched_lead = await crud.get_latest_lead_by_contact_email(db, email)
        if matched_lead:
            payment_client.lead_id = matched_lead.id
            matched_lead.status = "stage4_paid"

    await db.flush()

    detailed_audit = await crud.get_detailed_audit_by_client(db, payment_client.id)
    if not detailed_audit:
        detailed_audit = await crud.create_detailed_audit(db, payment_client.id)

    order_record.razorpay_payment_id = payment_id
    order_record.status = "paid"
    order_record.paid_at = now
    order_record.amount = amount_paid
    order_record.currency = currency
    order_record.legacy_client_id = payment_client.id

    selected_search = await crud.get_search_by_id(db, order_record.search_id) if order_record.search_id else None
    await _sync_client_with_selected_search(db, payment_client, selected_search)
    order_record.legacy_lead_id = payment_client.lead_id or order_record.legacy_lead_id

    audit_job = await crud.get_audit_job_by_order_id(db, order_record.id)
    if not audit_job:
        audit_job = await crud.create_audit_job_record(
            db,
            user_id=user.id if user else None,
            search_id=order_record.search_id,
            order_id=order_record.id,
            legacy_client_id=payment_client.id,
            legacy_detailed_audit_id=detailed_audit.id if detailed_audit else None,
            audit_status=payment_client.audit_status,
            access_expires_at=payment_client.access_expires_at,
            report_approved=detailed_audit.report_approved if detailed_audit else False,
            report_pdf_path=detailed_audit.report_pdf_path if detailed_audit else None,
        )
    else:
        audit_job.audit_status = payment_client.audit_status
        audit_job.access_expires_at = payment_client.access_expires_at
        audit_job.legacy_client_id = payment_client.id
        audit_job.legacy_detailed_audit_id = (
            detailed_audit.id if detailed_audit else audit_job.legacy_detailed_audit_id
        )
        if detailed_audit:
            audit_job.report_approved = detailed_audit.report_approved
            audit_job.report_pdf_path = detailed_audit.report_pdf_path

    return now, detailed_audit, audit_job


class CreateOrderRequest(BaseModel):
    plan_type: str = "basic_audit"
    search_id: Optional[int] = None


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


@router.post("/payment/create-order")
async def create_order(
    req: CreateOrderRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    email = _get_current_email(request)
    if not email:
        raise HTTPException(401, "Please log in before purchasing.")

    account_client = await crud.get_client_by_email(db, email)
    if not account_client:
        raise HTTPException(404, "Account not found. Please register first.")

    user = await crud.get_user_by_email(db, email)
    search = None
    if req.search_id:
        search = await crud.get_search_by_id(db, req.search_id)
        if not search:
            raise HTTPException(404, "Saved search not found.")
        if search and user and search.user_id not in (None, user.id):
            raise HTTPException(403, "This search does not belong to the current user.")
    elif user:
        search = await crud.get_latest_search_for_user(db, user.id)

    payment_client = await _resolve_payment_client_for_search(db, account_client, search, req.plan_type)

    try:
        rz = _razorpay_client()
        receipt_search = search.id if search else "latest"
        receipt_stamp = int(datetime.now(timezone.utc).timestamp())
        order = rz.order.create(
            {
                "amount": AUDIT_PRICE_PAISE,
                "currency": "INR",
                "receipt": f"aidbro_{payment_client.id}_{receipt_search}_{receipt_stamp}",
                "notes": {
                    "client_id": str(payment_client.id),
                    "client_email": email,
                    "plan_type": req.plan_type,
                    "search_id": str(search.id) if search else "",
                    "legacy_lead_id": str(search.legacy_lead_id) if search and search.legacy_lead_id else "",
                },
            }
        )
    except Exception as exc:
        raise HTTPException(500, f"Could not create payment order: {str(exc)}")

    await crud.create_payment_order_record(
        db,
        user_id=user.id if user else None,
        search_id=search.id if search else None,
        legacy_client_id=payment_client.id,
        legacy_lead_id=payment_client.lead_id or (search.legacy_lead_id if search else None),
        razorpay_order_id=order["id"],
        amount=AUDIT_PRICE_INR,
        currency="INR",
        status="created",
        plan_type=req.plan_type,
    )

    if user:
        await crud.create_user_activity(
            db,
            user.id,
            "payment_order_created",
            {
                "search_id": search.id if search else None,
                "razorpay_order_id": order["id"],
                "amount": AUDIT_PRICE_INR,
            },
        )

    return JSONResponse(
        content={
            "order_id": order["id"],
            "amount": AUDIT_PRICE_PAISE,
            "currency": "INR",
            "key_id": RAZORPAY_KEY_ID,
            "business_name": "Aidbro - Reals Digital Innovations",
            "description": f"Digital Health Detailed Audit - Rs {AUDIT_PRICE_INR}",
            "prefill_email": email,
        }
    )


@router.post("/payment/verify")
async def verify_payment(
    req: VerifyPaymentRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    email = _get_current_email(request)
    if not email:
        raise HTTPException(401, "Not authenticated.")

    expected_sig = hmac.new(
        RAZORPAY_KEY_SECRET.encode(),
        f"{req.razorpay_order_id}|{req.razorpay_payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected_sig, req.razorpay_signature):
        raise HTTPException(400, "Payment verification failed - invalid signature.")

    user = await crud.get_user_by_email(db, email)
    account_client = await crud.get_client_by_email(db, email)
    if not account_client:
        raise HTTPException(404, "Account not found.")

    order_record = await crud.get_payment_order_by_razorpay_order_id(db, req.razorpay_order_id)
    if not order_record:
        latest_search = await crud.get_latest_search_for_user(db, user.id) if user else None
        order_record = await crud.create_payment_order_record(
            db,
            user_id=user.id if user else None,
            search_id=latest_search.id if latest_search else None,
            legacy_client_id=account_client.id,
            legacy_lead_id=account_client.lead_id or (latest_search.legacy_lead_id if latest_search else None),
            razorpay_order_id=req.razorpay_order_id,
            amount=AUDIT_PRICE_INR,
            currency="INR",
            status="created",
            plan_type="basic_audit",
        )

    payment_client = (
        await crud.get_client_by_id(db, order_record.legacy_client_id)
        if order_record.legacy_client_id
        else account_client
    )
    if not payment_client:
        payment_client = account_client

    _, _, audit_job = await _upsert_payment_success(
        db,
        payment_client=payment_client,
        user=user,
        order_record=order_record,
        email=email,
        payment_id=req.razorpay_payment_id,
        amount_paid=AUDIT_PRICE_INR,
        currency="INR",
    )

    if user:
        await crud.create_user_activity(
            db,
            user.id,
            "payment_verified",
            {
                "search_id": order_record.search_id,
                "order_id": order_record.razorpay_order_id,
                "payment_id": req.razorpay_payment_id,
                "audit_job_id": audit_job.id,
            },
        )

    return JSONResponse(
        content={
            "success": True,
            "message": "Payment confirmed! Your detailed audit portal is now active.",
            "audit_status": "pending",
            "access_until": payment_client.access_expires_at.isoformat(),
        }
    )


@router.post("/payment/webhook")
async def payment_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    if RAZORPAY_WEBHOOK_SECRET:
        expected = hmac.new(
            RAZORPAY_WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise HTTPException(400, "Invalid webhook signature")

    try:
        event = json.loads(body)
        if event.get("event") == "payment.captured":
            payment = event["payload"]["payment"]["entity"]
            notes = payment.get("notes", {})
            email = notes.get("client_email")

            if email:
                user = await crud.get_user_by_email(db, email)
                account_client = await crud.get_client_by_email(db, email)
                if not account_client:
                    return JSONResponse(content={"status": "ok"})

                order_record = await crud.get_payment_order_by_razorpay_order_id(db, payment["order_id"])
                if not order_record:
                    fallback_search = None
                    if notes.get("search_id"):
                        try:
                            fallback_search = await crud.get_search_by_id(db, int(notes["search_id"]))
                        except (TypeError, ValueError):
                            fallback_search = None
                    if not fallback_search and user:
                        fallback_search = await crud.get_latest_search_for_user(db, user.id)

                    legacy_client_id = account_client.id
                    if notes.get("client_id"):
                        try:
                            legacy_client_id = int(notes["client_id"])
                        except (TypeError, ValueError):
                            legacy_client_id = account_client.id

                    order_record = await crud.create_payment_order_record(
                        db,
                        user_id=user.id if user else None,
                        search_id=fallback_search.id if fallback_search else None,
                        legacy_client_id=legacy_client_id,
                        legacy_lead_id=account_client.lead_id or (fallback_search.legacy_lead_id if fallback_search else None),
                        razorpay_order_id=payment["order_id"],
                        amount=payment["amount"] / 100,
                        currency=payment.get("currency", "INR"),
                        status="captured",
                        plan_type=notes.get("plan_type", "basic_audit"),
                    )

                payment_client = (
                    await crud.get_client_by_id(db, order_record.legacy_client_id)
                    if order_record.legacy_client_id
                    else account_client
                )
                if not payment_client:
                    payment_client = account_client

                _, _, audit_job = await _upsert_payment_success(
                    db,
                    payment_client=payment_client,
                    user=user,
                    order_record=order_record,
                    email=email,
                    payment_id=payment["id"],
                    amount_paid=payment["amount"] / 100,
                    currency=payment.get("currency", "INR"),
                )

                if user:
                    await crud.create_user_activity(
                        db,
                        user.id,
                        "payment_captured_webhook",
                        {
                            "search_id": order_record.search_id,
                            "order_id": order_record.razorpay_order_id,
                            "payment_id": payment["id"],
                            "audit_job_id": audit_job.id,
                        },
                    )
    except Exception as exc:
        print(f"[Webhook] Error processing: {exc}")

    return JSONResponse(content={"status": "ok"})


@router.get("/payment/status")
async def payment_status(
    request: Request,
    search_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    email = _get_current_email(request)
    if not email:
        return JSONResponse(
            content={
                "has_paid": False,
                "audit_status": "unsubscribed",
                "plan_type": "none",
                "amount_paid": None,
                "paid_at": None,
                "access_until": None,
                "price_inr": AUDIT_PRICE_INR,
                "razorpay_key": RAZORPAY_KEY_ID,
            }
        )

    client_obj = await crud.get_client_by_email(db, email)
    user = await crud.get_user_by_email(db, email)

    if search_id is not None:
        if not user:
            raise HTTPException(404, "User account not found.")
        search = await crud.get_search_by_id(db, search_id)
        if not search:
            raise HTTPException(404, "Saved search not found.")
        if search.user_id != user.id:
            raise HTTPException(403, "This search does not belong to the current user.")

        audit_job = await crud.get_latest_audit_job_for_search(db, search.id, user.id)
        return JSONResponse(
            content={
                "has_paid": audit_job is not None,
                "account_has_paid": client_obj.paid_at is not None if client_obj else False,
                "audit_status": audit_job.audit_status if audit_job else "unsubscribed",
                "plan_type": "basic_audit" if audit_job else "none",
                "amount_paid": AUDIT_PRICE_INR if audit_job else None,
                "paid_at": audit_job.created_at.isoformat() if audit_job and audit_job.created_at else None,
                "access_until": (
                    audit_job.access_expires_at.isoformat()
                    if audit_job and audit_job.access_expires_at
                    else None
                ),
                "price_inr": AUDIT_PRICE_INR,
                "razorpay_key": RAZORPAY_KEY_ID,
                "search_id": search.id,
                "audit_job_id": audit_job.id if audit_job else None,
            }
        )

    if not client_obj:
        raise HTTPException(404, "Account not found.")

    return JSONResponse(
        content={
            "has_paid": client_obj.paid_at is not None,
            "audit_status": client_obj.audit_status,
            "plan_type": client_obj.plan_type,
            "amount_paid": float(client_obj.amount_paid) if client_obj.amount_paid else None,
            "paid_at": client_obj.paid_at.isoformat() if client_obj.paid_at else None,
            "access_until": client_obj.access_expires_at.isoformat() if client_obj.access_expires_at else None,
            "price_inr": AUDIT_PRICE_INR,
            "razorpay_key": RAZORPAY_KEY_ID,
        }
    )
