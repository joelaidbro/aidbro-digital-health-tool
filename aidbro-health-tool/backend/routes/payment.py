"""
Payment Routes
==============
POST /api/payment/create-order   — Create Razorpay order (requires auth)
POST /api/payment/verify         — Verify payment after checkout completes
POST /api/payment/webhook        — Razorpay webhook (server-to-server)
GET  /api/payment/status         — Check current subscription status
"""

import os
import hmac
import hashlib
import razorpay
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from database import crud
from utils.auth_utils import decode_token

router = APIRouter()

# ── Razorpay config ───────────────────────────────────────────────────────────
RAZORPAY_KEY_ID     = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", RAZORPAY_KEY_SECRET)
AUDIT_PRICE_INR     = int(os.getenv("AUDIT_PRICE_INR", "2000"))   # in rupees
AUDIT_PRICE_PAISE   = AUDIT_PRICE_INR * 100                        # Razorpay uses paise
PORTAL_ACCESS_DAYS  = int(os.getenv("PORTAL_ACCESS_DAYS", "90"))


def _razorpay_client():
    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        raise HTTPException(500, "Razorpay not configured. Add keys to .env")
    return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


def _get_current_email(request: Request) -> Optional[str]:
    """Extract email from JWT in Authorization header."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    payload = decode_token(auth[7:])
    return payload.get("sub") if payload else None


# ── Request models ────────────────────────────────────────────────────────────

class CreateOrderRequest(BaseModel):
    plan_type: str = "basic_audit"   # basic_audit | detailed_audit
    search_id: Optional[int] = None


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id:   str
    razorpay_payment_id: str
    razorpay_signature:  str


# ── CREATE ORDER ──────────────────────────────────────────────────────────────

@router.post("/payment/create-order")
async def create_order(
    req: CreateOrderRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Creates a Razorpay order and returns the order_id + key_id
    so the frontend can open the Razorpay checkout modal.
    Requires the user to be logged in (JWT in header).
    """
    email = _get_current_email(request)
    if not email:
        raise HTTPException(401, "Please log in before purchasing.")

    client_obj = await crud.get_client_by_email(db, email)
    if not client_obj:
        raise HTTPException(404, "Account not found. Please register first.")
    user = await crud.get_user_by_email(db, email)
    search = None
    if req.search_id:
        search = await crud.get_search_by_id(db, req.search_id)
        if search and user and search.user_id not in (None, user.id):
            raise HTTPException(403, "This search does not belong to the current user.")
    elif user:
        search = await crud.get_latest_search_for_user(db, user.id)

    # Don't charge twice
    if client_obj.paid_at is not None:
        raise HTTPException(400, "You have already purchased a detailed audit.")

    try:
        rz    = _razorpay_client()
        order = rz.order.create({
            "amount":   AUDIT_PRICE_PAISE,
            "currency": "INR",
            "receipt":  f"aidbro_{client_obj.id}",
            "notes": {
                "client_id":  str(client_obj.id),
                "client_email": email,
                "plan_type":  req.plan_type,
            },
        })
    except Exception as e:
        raise HTTPException(500, f"Could not create payment order: {str(e)}")

    await crud.create_payment_order_record(
        db,
        user_id=user.id if user else None,
        search_id=search.id if search else None,
        legacy_client_id=client_obj.id,
        legacy_lead_id=client_obj.lead_id or (search.legacy_lead_id if search else None),
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

    return JSONResponse(content={
        "order_id":     order["id"],
        "amount":       AUDIT_PRICE_PAISE,
        "currency":     "INR",
        "key_id":       RAZORPAY_KEY_ID,
        "business_name": "Aidbro — Reals Digital Innovations",
        "description":  f"Digital Health Detailed Audit — ₹{AUDIT_PRICE_INR}",
        "prefill_email": email,
    })


# ── VERIFY PAYMENT (client-side confirmation) ─────────────────────────────────

@router.post("/payment/verify")
async def verify_payment(
    req: VerifyPaymentRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Called by frontend after Razorpay checkout succeeds.
    Verifies signature and unlocks portal access.
    """
    email = _get_current_email(request)
    if not email:
        raise HTTPException(401, "Not authenticated.")

    # ── Verify Razorpay signature ─────────────────────────────────────────────
    expected_sig = hmac.new(
        RAZORPAY_KEY_SECRET.encode(),
        f"{req.razorpay_order_id}|{req.razorpay_payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_sig, req.razorpay_signature):
        raise HTTPException(400, "Payment verification failed — invalid signature.")

    # ── Unlock the account ────────────────────────────────────────────────────
    client_obj = await crud.get_client_by_email(db, email)
    if not client_obj:
        raise HTTPException(404, "Account not found.")
    user = await crud.get_user_by_email(db, email)

    now = datetime.now(timezone.utc)
    client_obj.payment_id        = req.razorpay_payment_id
    client_obj.order_id          = req.razorpay_order_id
    client_obj.amount_paid       = AUDIT_PRICE_INR
    client_obj.paid_at           = now
    client_obj.plan_type         = "basic_audit"
    client_obj.audit_status      = "pending"
    client_obj.access_expires_at = now + timedelta(days=PORTAL_ACCESS_DAYS)

    if not client_obj.lead_id:
        matched_lead = await crud.get_latest_lead_by_contact_email(db, email)
        if matched_lead:
            client_obj.lead_id = matched_lead.id
            matched_lead.status = "stage4_paid"

    await db.flush()

    # ── Create empty detailed audit record ───────────────────────────────────
    existing_audit = await crud.get_detailed_audit_by_client(db, client_obj.id)
    if not existing_audit:
        existing_audit = await crud.create_detailed_audit(db, client_obj.id)

    order_record = await crud.get_payment_order_by_razorpay_order_id(db, req.razorpay_order_id)
    if not order_record:
        latest_search = await crud.get_latest_search_for_user(db, user.id) if user else None
        order_record = await crud.create_payment_order_record(
            db,
            user_id=user.id if user else None,
            search_id=latest_search.id if latest_search else None,
            legacy_client_id=client_obj.id,
            legacy_lead_id=client_obj.lead_id or (latest_search.legacy_lead_id if latest_search else None),
            razorpay_order_id=req.razorpay_order_id,
            amount=AUDIT_PRICE_INR,
            currency="INR",
            status="created",
            plan_type="basic_audit",
        )

    order_record.razorpay_payment_id = req.razorpay_payment_id
    order_record.status = "paid"
    order_record.paid_at = now
    order_record.amount = AUDIT_PRICE_INR
    order_record.currency = "INR"
    order_record.legacy_client_id = client_obj.id
    order_record.legacy_lead_id = client_obj.lead_id or order_record.legacy_lead_id

    audit_job = await crud.get_audit_job_by_order_id(db, order_record.id)
    if not audit_job:
        audit_job = await crud.create_audit_job_record(
            db,
            user_id=user.id if user else None,
            search_id=order_record.search_id,
            order_id=order_record.id,
            legacy_client_id=client_obj.id,
            legacy_detailed_audit_id=existing_audit.id if existing_audit else None,
            audit_status=client_obj.audit_status,
            access_expires_at=client_obj.access_expires_at,
            report_approved=existing_audit.report_approved if existing_audit else False,
            report_pdf_path=existing_audit.report_pdf_path if existing_audit else None,
        )
    else:
        audit_job.audit_status = client_obj.audit_status
        audit_job.access_expires_at = client_obj.access_expires_at
        audit_job.legacy_client_id = client_obj.id
        audit_job.legacy_detailed_audit_id = existing_audit.id if existing_audit else audit_job.legacy_detailed_audit_id
        if existing_audit:
            audit_job.report_approved = existing_audit.report_approved
            audit_job.report_pdf_path = existing_audit.report_pdf_path

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

    return JSONResponse(content={
        "success":      True,
        "message":      "Payment confirmed! Your detailed audit portal is now active.",
        "audit_status": "pending",
        "access_until": client_obj.access_expires_at.isoformat(),
    })


# ── RAZORPAY WEBHOOK (server-to-server backup) ───────────────────────────────

@router.post("/payment/webhook")
async def payment_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Razorpay sends this to the backend directly as a backup
    in case the client browser closed before /verify was called.
    Configure this URL in Razorpay Dashboard → Webhooks.
    """
    body      = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    # Verify webhook signature
    if RAZORPAY_WEBHOOK_SECRET:
        expected = hmac.new(
            RAZORPAY_WEBHOOK_SECRET.encode(), body, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise HTTPException(400, "Invalid webhook signature")

    try:
        import json
        event = json.loads(body)
        ev_type = event.get("event")

        if ev_type == "payment.captured":
            payment = event["payload"]["payment"]["entity"]
            notes   = payment.get("notes", {})
            email   = notes.get("client_email")

            if email:
                client_obj = await crud.get_client_by_email(db, email)
                if client_obj and client_obj.paid_at is None:
                    user = await crud.get_user_by_email(db, email)
                    now = datetime.now(timezone.utc)
                    client_obj.payment_id        = payment["id"]
                    client_obj.amount_paid       = payment["amount"] / 100
                    client_obj.paid_at           = now
                    client_obj.plan_type         = "basic_audit"
                    client_obj.audit_status      = "pending"
                    client_obj.access_expires_at = now + timedelta(days=PORTAL_ACCESS_DAYS)

                    if not client_obj.lead_id:
                        matched_lead = await crud.get_latest_lead_by_contact_email(db, email)
                        if matched_lead:
                            client_obj.lead_id = matched_lead.id
                            matched_lead.status = "stage4_paid"

                    await db.flush()

                    existing_audit = await crud.get_detailed_audit_by_client(db, client_obj.id)
                    if not existing_audit:
                        existing_audit = await crud.create_detailed_audit(db, client_obj.id)

                    order_record = await crud.get_payment_order_by_razorpay_order_id(db, payment["order_id"])
                    if not order_record:
                        latest_search = await crud.get_latest_search_for_user(db, user.id) if user else None
                        order_record = await crud.create_payment_order_record(
                            db,
                            user_id=user.id if user else None,
                            search_id=latest_search.id if latest_search else None,
                            legacy_client_id=client_obj.id,
                            legacy_lead_id=client_obj.lead_id or (latest_search.legacy_lead_id if latest_search else None),
                            razorpay_order_id=payment["order_id"],
                            amount=payment["amount"] / 100,
                            currency=payment.get("currency", "INR"),
                            status="captured",
                            plan_type=notes.get("plan_type", "basic_audit"),
                        )

                    order_record.razorpay_payment_id = payment["id"]
                    order_record.status = "paid"
                    order_record.paid_at = now
                    order_record.amount = payment["amount"] / 100
                    order_record.currency = payment.get("currency", "INR")
                    order_record.legacy_client_id = client_obj.id
                    order_record.legacy_lead_id = client_obj.lead_id or order_record.legacy_lead_id

                    audit_job = await crud.get_audit_job_by_order_id(db, order_record.id)
                    if not audit_job:
                        await crud.create_audit_job_record(
                            db,
                            user_id=user.id if user else None,
                            search_id=order_record.search_id,
                            order_id=order_record.id,
                            legacy_client_id=client_obj.id,
                            legacy_detailed_audit_id=existing_audit.id if existing_audit else None,
                            audit_status=client_obj.audit_status,
                            access_expires_at=client_obj.access_expires_at,
                            report_approved=existing_audit.report_approved if existing_audit else False,
                            report_pdf_path=existing_audit.report_pdf_path if existing_audit else None,
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
                            },
                        )

                    print(f"[Webhook] Payment captured for {email}")

    except Exception as e:
        print(f"[Webhook] Error processing: {e}")

    # Always return 200 to Razorpay
    return JSONResponse(content={"status": "ok"})


# ── GET PAYMENT / SUBSCRIPTION STATUS ────────────────────────────────────────

@router.get("/payment/status")
async def payment_status(request: Request, db: AsyncSession = Depends(get_db)):
    """Returns current subscription + audit status for the logged-in user."""
    email = _get_current_email(request)
    if not email:
        return JSONResponse(content={
            "has_paid": False,
            "audit_status": "unsubscribed",
            "plan_type": "none",
            "amount_paid": None,
            "paid_at": None,
            "access_until": None,
            "price_inr": AUDIT_PRICE_INR,
            "razorpay_key": RAZORPAY_KEY_ID,
        })

    client_obj = await crud.get_client_by_email(db, email)
    if not client_obj:
        raise HTTPException(404, "Account not found.")

    return JSONResponse(content={
        "has_paid":     client_obj.paid_at is not None,
        "audit_status": client_obj.audit_status,
        "plan_type":    client_obj.plan_type,
        "amount_paid":  float(client_obj.amount_paid) if client_obj.amount_paid else None,
        "paid_at":      client_obj.paid_at.isoformat() if client_obj.paid_at else None,
        "access_until": client_obj.access_expires_at.isoformat() if client_obj.access_expires_at else None,
        "price_inr":    AUDIT_PRICE_INR,
        "razorpay_key": RAZORPAY_KEY_ID,
    })
