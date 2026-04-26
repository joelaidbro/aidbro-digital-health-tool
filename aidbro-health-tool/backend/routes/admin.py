from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import crud
from database.connection import get_db
from database.models import (
    AdminUser,
    AuditClient,
    AuditJob,
    DetailedAudit,
    Lead,
    PaymentOrder,
    SearchRecord,
    UserAccount,
    UserActivityLog,
)
from utils.auth_utils import decode_token, hash_password

router = APIRouter()

ADMIN_ROLES = {"super_admin", "manager", "analyst", "admin"}
APPROVER_ROLES = {"super_admin", "manager", "admin"}
LEAD_STATUSES = {
    "new",
    "contacted",
    "demo_done",
    "stage4_paid",
    "service_signed",
    "not_interested",
    "follow_up",
}
AUDIT_STATUSES = {"pending", "in_progress", "review", "completed", "delivered"}
AUDIT_SORT_ORDER = {
    "pending": 0,
    "in_progress": 1,
    "review": 2,
    "completed": 3,
    "delivered": 4,
}
ACTIVITY_ALERT_WINDOW_HOURS = 24
ACTIVITY_ALERT_THRESHOLD = 8


class LeadUpdateRequest(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    assigned_to: Optional[str] = None
    follow_up_date: Optional[str] = None


class OverrideInput(BaseModel):
    section: str
    field_name: str
    original_value: Any = None
    override_value: Any = None
    reason: str = ""


class AuditWorkspaceUpdate(BaseModel):
    audit_status: Optional[str] = None
    analyst_notes: Optional[str] = None
    ai_synthesis_json: Optional[dict] = None
    instagram_manual: Optional[dict] = None
    facebook_manual: Optional[dict] = None
    linkedin_manual: Optional[dict] = None
    overrides: list[OverrideInput] = []


class ApproveAuditRequest(BaseModel):
    report_pdf_path: Optional[str] = None


class CreateAdminRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "analyst"


class UpdateAdminRequest(BaseModel):
    is_active: Optional[bool] = None
    role: Optional[str] = None


def _json_safe(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    return value


def _extract_token(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, "Admin authentication required.")
    return auth[7:]


def _require_admin_payload(request: Request, allowed_roles: Optional[set[str]] = None) -> dict:
    payload = decode_token(_extract_token(request), is_admin=True)
    if not payload:
        raise HTTPException(401, "Invalid or expired admin token.")

    role = payload.get("role")
    if role not in ADMIN_ROLES:
        raise HTTPException(403, "Admin access required.")
    if allowed_roles and role not in allowed_roles:
        raise HTTPException(403, "You do not have permission for this action.")
    return payload


async def _require_admin_user(
    request: Request,
    db: AsyncSession,
    allowed_roles: Optional[set[str]] = None,
) -> AdminUser:
    payload = _require_admin_payload(request, allowed_roles)
    admin = await crud.get_admin_by_email(db, payload.get("sub", ""))
    if not admin or not admin.is_active:
        raise HTTPException(401, "Admin account not found or inactive.")
    return admin


async def _match_lead_for_client(db: AsyncSession, client: AuditClient) -> Optional[Lead]:
    if client.lead_id:
        return await crud.get_lead_by_id(db, client.lead_id)

    matched = await crud.get_latest_lead_by_contact_email(db, client.email)
    if matched:
        client.lead_id = matched.id
        if matched.status == "new":
            matched.status = "stage4_paid"
        await db.flush()
    return matched


def _build_local_seo_snapshot(lead_audit_json: dict) -> dict:
    business = lead_audit_json.get("business", {}) if lead_audit_json else {}
    return {
        "maps_url": business.get("maps_url"),
        "address": business.get("address"),
        "rating": business.get("rating"),
        "total_reviews": business.get("total_reviews"),
        "category": business.get("category"),
        "location": business.get("location"),
    }


async def _get_latest_paid_search_for_client(
    db: AsyncSession,
    client: AuditClient,
) -> Optional[SearchRecord]:
    audit_job = (
        await db.execute(
            select(AuditJob)
            .where(AuditJob.legacy_client_id == client.id, AuditJob.search_id.isnot(None))
            .order_by(desc(AuditJob.created_at))
            .limit(1)
        )
    ).scalar_one_or_none()
    if audit_job and audit_job.search_id:
        return await crud.get_search_by_id(db, audit_job.search_id)

    order = (
        await db.execute(
            select(PaymentOrder)
            .where(PaymentOrder.legacy_client_id == client.id, PaymentOrder.search_id.isnot(None))
            .order_by(desc(PaymentOrder.created_at))
            .limit(1)
        )
    ).scalar_one_or_none()
    if order and order.search_id:
        return await crud.get_search_by_id(db, order.search_id)

    return None


async def _ensure_audit_workspace(
    db: AsyncSession,
    client: AuditClient,
) -> tuple[Optional[Lead], DetailedAudit]:
    lead = await _match_lead_for_client(db, client)
    paid_search = await _get_latest_paid_search_for_client(db, client)

    detailed = await crud.get_detailed_audit_by_client(db, client.id)
    if not detailed:
        detailed = await crud.create_detailed_audit(db, client.id)

    source_audit_json = {}
    if lead and lead.audit_json:
        source_audit_json = lead.audit_json
    elif paid_search and paid_search.audit_json:
        source_audit_json = paid_search.audit_json

    should_seed = bool(source_audit_json) and not any(
        [
            detailed.basic_audit_json,
            detailed.seo_crawler_json,
            detailed.competitors_json,
            detailed.keywords_json,
            detailed.local_seo_json,
        ]
    )

    if should_seed:
        detailed.basic_audit_json = {
            "business": source_audit_json.get("business"),
            "score": source_audit_json.get("score"),
            "pagespeed": source_audit_json.get("pagespeed"),
            "social": source_audit_json.get("social"),
            "insights": source_audit_json.get("insights"),
        }
        detailed.seo_crawler_json = source_audit_json.get("seo")
        detailed.competitors_json = source_audit_json.get("competitors")
        detailed.keywords_json = source_audit_json.get("keywords")
        detailed.local_seo_json = _build_local_seo_snapshot(source_audit_json)
        detailed.updated_at = datetime.now(timezone.utc)
        await db.flush()

    return lead, detailed


def _serialize_client(client: AuditClient) -> dict:
    return {
        "id": client.id,
        "email": client.email,
        "lead_id": client.lead_id,
        "plan_type": client.plan_type,
        "audit_status": client.audit_status,
        "amount_paid": float(client.amount_paid) if client.amount_paid is not None else None,
        "currency": client.currency,
        "paid_at": client.paid_at.isoformat() if client.paid_at else None,
        "audit_started_at": client.audit_started_at.isoformat() if client.audit_started_at else None,
        "audit_completed_at": client.audit_completed_at.isoformat() if client.audit_completed_at else None,
        "report_delivered_at": client.report_delivered_at.isoformat() if client.report_delivered_at else None,
        "access_expires_at": client.access_expires_at.isoformat() if client.access_expires_at else None,
        "credentials_sent_at": client.credentials_sent_at.isoformat() if client.credentials_sent_at else None,
        "report_ready_sent_at": client.report_ready_sent_at.isoformat() if client.report_ready_sent_at else None,
    }


def _serialize_detailed_audit(audit: DetailedAudit) -> dict:
    return {
        "id": audit.id,
        "client_id": audit.client_id,
        "created_at": audit.created_at.isoformat() if audit.created_at else None,
        "updated_at": audit.updated_at.isoformat() if audit.updated_at else None,
        "basic_audit_json": _json_safe(audit.basic_audit_json),
        "seo_crawler_json": _json_safe(audit.seo_crawler_json),
        "competitors_json": _json_safe(audit.competitors_json),
        "keywords_json": _json_safe(audit.keywords_json),
        "local_seo_json": _json_safe(audit.local_seo_json),
        "basic_audit_overrides": _json_safe(audit.basic_audit_overrides or {}),
        "seo_overrides": _json_safe(audit.seo_overrides or {}),
        "competitors_overrides": _json_safe(audit.competitors_overrides or {}),
        "keywords_overrides": _json_safe(audit.keywords_overrides or {}),
        "local_seo_overrides": _json_safe(audit.local_seo_overrides or {}),
        "instagram_manual": _json_safe(audit.instagram_manual),
        "facebook_manual": _json_safe(audit.facebook_manual),
        "linkedin_manual": _json_safe(audit.linkedin_manual),
        "analyst_notes": audit.analyst_notes,
        "analyst_name": audit.analyst_name,
        "ai_synthesis_json": _json_safe(audit.ai_synthesis_json),
        "report_approved": audit.report_approved,
        "approved_by": audit.approved_by,
        "approved_at": audit.approved_at.isoformat() if audit.approved_at else None,
        "report_pdf_path": audit.report_pdf_path,
        "last_edited_by": audit.last_edited_by,
        "last_edited_at": audit.last_edited_at.isoformat() if audit.last_edited_at else None,
    }


def _serialize_search(search: SearchRecord) -> dict:
    return _json_safe(search.to_dict())


def _serialize_user_account(user: UserAccount) -> dict:
    return _json_safe(user.to_dict())


def _serialize_audit_job(job: AuditJob) -> dict:
    return _json_safe(job.to_dict())


def _search_as_lead_like(search: SearchRecord) -> dict:
    return {
        "id": None,
        "business_name": search.business_name,
        "location": search.location,
        "category": search.category,
        "website_url": search.website_url,
        "contact_phone": search.auto_phone,
        "contact_email": search.auto_email,
        "total_score": search.total_score,
        "grade": search.grade,
        "score_label": search.score_label,
        "status": search.status,
        "audit_json": _json_safe(search.audit_json or {}),
        "created_at": search.created_at.isoformat() if search.created_at else None,
        "is_mocked": search.is_mocked,
    }


def _override_column_for_section(section: str) -> Optional[str]:
    return {
        "basic_audit": "basic_audit_overrides",
        "seo": "seo_overrides",
        "competitors": "competitors_overrides",
        "keywords": "keywords_overrides",
        "local_seo": "local_seo_overrides",
    }.get(section)


@router.get("/admin/dashboard")
async def admin_dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    await _require_admin_user(request, db)

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = (today_start - timedelta(days=today_start.weekday()))
    month_start = today_start.replace(day=1)
    activity_window_start = now - timedelta(hours=ACTIVITY_ALERT_WINDOW_HOURS)

    leads_total = (await db.execute(select(func.count(Lead.id)))).scalar_one()
    leads_contact = (
        await db.execute(select(func.count(Lead.id)).where(Lead.contact_email.isnot(None)))
    ).scalar_one()
    searches_total = (await db.execute(select(func.count(SearchRecord.id)))).scalar_one()
    anonymous_searches = (
        await db.execute(select(func.count(SearchRecord.id)).where(SearchRecord.user_id.is_(None)))
    ).scalar_one()
    registered_users = (
        await db.execute(select(func.count(UserAccount.id)).where(UserAccount.is_active.is_(True)))
    ).scalar_one()
    paid_clients = (
        await db.execute(select(func.count(AuditClient.id)).where(AuditClient.paid_at.isnot(None)))
    ).scalar_one()
    audits_today = (
        await db.execute(
            select(func.count(AuditClient.id)).where(AuditClient.paid_at.isnot(None), AuditClient.paid_at >= today_start)
        )
    ).scalar_one()
    audits_week = (
        await db.execute(
            select(func.count(AuditClient.id)).where(AuditClient.paid_at.isnot(None), AuditClient.paid_at >= week_start)
        )
    ).scalar_one()
    audits_month = (
        await db.execute(
            select(func.count(AuditClient.id)).where(AuditClient.paid_at.isnot(None), AuditClient.paid_at >= month_start)
        )
    ).scalar_one()
    revenue_month = (
        await db.execute(
            select(func.sum(AuditClient.amount_paid)).where(AuditClient.paid_at.isnot(None), AuditClient.paid_at >= month_start)
        )
    ).scalar_one()

    funnel_rows = (
        await db.execute(
            select(Lead.status, func.count(Lead.id))
            .group_by(Lead.status)
            .order_by(Lead.status)
        )
    ).all()
    funnel = [{"status": status, "count": count} for status, count in funnel_rows]

    audit_rows = (
        await db.execute(
            select(AuditClient.audit_status, func.count(AuditClient.id))
            .where(AuditClient.paid_at.isnot(None))
            .group_by(AuditClient.audit_status)
        )
    ).all()
    audit_pipeline = [{"status": status, "count": count} for status, count in audit_rows]

    category_rows = (
        await db.execute(
            select(
                Lead.category,
                func.avg(Lead.total_score),
                func.count(Lead.id),
            )
            .where(Lead.total_score.isnot(None))
            .group_by(Lead.category)
            .order_by(desc(func.avg(Lead.total_score)))
        )
    ).all()
    score_by_category = [
        {
            "category": category or "Uncategorized",
            "avg_score": round(float(avg_score or 0), 1),
            "count": count,
        }
        for category, avg_score, count in category_rows
    ]

    score_values = list(
        (
            await db.execute(
                select(Lead.total_score).where(Lead.total_score.isnot(None))
            )
        ).scalars().all()
    )
    score_distribution = [
        {"label": "0-39", "count": sum(1 for score in score_values if 0 <= score <= 39)},
        {"label": "40-59", "count": sum(1 for score in score_values if 40 <= score <= 59)},
        {"label": "60-79", "count": sum(1 for score in score_values if 60 <= score <= 79)},
        {"label": "80-100", "count": sum(1 for score in score_values if 80 <= score <= 100)},
    ]

    search_sources = [
        {"label": "Anonymous", "count": anonymous_searches},
        {"label": "Logged In", "count": max(searches_total - anonymous_searches, 0)},
    ]
    ip_alerts = await crud.get_high_activity_ip_rows(
        db,
        since=activity_window_start,
        threshold=ACTIVITY_ALERT_THRESHOLD,
        limit=6,
    )
    account_alerts = await crud.get_high_activity_user_rows(
        db,
        since=activity_window_start,
        threshold=ACTIVITY_ALERT_THRESHOLD,
        limit=6,
    )

    return JSONResponse(
        content={
            "metrics": {
                "leads_total": leads_total,
                "leads_with_contact": leads_contact,
                "searches_total": searches_total,
                "anonymous_searches": anonymous_searches,
                "registered_users": registered_users,
                "paid_clients": paid_clients,
                "conversion_rate": round((paid_clients / searches_total) * 100, 1) if searches_total else 0,
                "audits_today": audits_today,
                "audits_week": audits_week,
                "audits_month": audits_month,
                "revenue_month": float(revenue_month or 0),
                "high_activity_alerts": len(ip_alerts) + len(account_alerts),
            },
            "funnel": funnel,
            "audit_pipeline": audit_pipeline,
            "score_by_category": score_by_category,
            "score_distribution": score_distribution,
            "search_sources": search_sources,
            "ip_alerts": ip_alerts,
            "account_alerts": account_alerts,
            "alert_window_hours": ACTIVITY_ALERT_WINDOW_HOURS,
            "alert_threshold": ACTIVITY_ALERT_THRESHOLD,
        }
    )


@router.get("/admin/leads")
async def admin_leads(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    min_score: Optional[int] = None,
    has_contact: Optional[bool] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    await _require_admin_user(request, db)

    query = select(Lead).order_by(desc(Lead.created_at))

    if status:
        query = query.where(Lead.status == status)
    if min_score is not None:
        query = query.where(Lead.total_score >= min_score)
    if has_contact is True:
        query = query.where(or_(Lead.contact_phone.isnot(None), Lead.contact_email.isnot(None)))
    if has_contact is False:
        query = query.where(Lead.contact_phone.is_(None), Lead.contact_email.is_(None))
    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(
            or_(
                Lead.business_name.ilike(pattern),
                Lead.location.ilike(pattern),
                Lead.category.ilike(pattern),
                Lead.contact_email.ilike(pattern),
            )
        )

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    rows = (await db.execute(query.limit(limit).offset(offset))).scalars().all()

    return JSONResponse(
        content={
            "total": total,
            "limit": limit,
            "offset": offset,
            "leads": [_json_safe(lead.to_dict()) for lead in rows],
        }
    )


@router.get("/admin/leads/{lead_id}")
async def admin_lead_detail(
    lead_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await _require_admin_user(request, db)

    lead = await crud.get_lead_by_id(db, lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found.")

    client = (
        await db.execute(select(AuditClient).where(AuditClient.lead_id == lead.id).limit(1))
    ).scalar_one_or_none()
    if not client and lead.contact_email:
        client = await crud.get_client_by_email(db, lead.contact_email)

    return JSONResponse(
        content={
            "lead": _json_safe({**lead.to_dict(), "audit_json": lead.audit_json}),
            "audit_client": _serialize_client(client) if client else None,
        }
    )


@router.patch("/admin/leads/{lead_id}")
async def admin_update_lead(
    lead_id: int,
    req: LeadUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    admin = await _require_admin_user(request, db)
    lead = await crud.get_lead_by_id(db, lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found.")

    if req.status is not None:
        if req.status not in LEAD_STATUSES:
            raise HTTPException(400, "Invalid lead status.")
        lead.status = req.status
    if req.notes is not None:
        lead.notes = req.notes
    if req.assigned_to is not None:
        lead.assigned_to = req.assigned_to
    if req.follow_up_date is not None:
        lead.follow_up_date = datetime.fromisoformat(req.follow_up_date) if req.follow_up_date else None

    if not lead.assigned_to:
        lead.assigned_to = admin.name

    await db.flush()
    await db.refresh(lead)

    return JSONResponse(content={"success": True, "lead": _json_safe(lead.to_dict())})


@router.get("/admin/anonymous-searches")
async def admin_anonymous_searches(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    min_score: Optional[int] = None,
    has_contact: Optional[bool] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    await _require_admin_user(request, db)

    query = (
        select(SearchRecord)
        .where(SearchRecord.user_id.is_(None))
        .order_by(desc(SearchRecord.created_at))
    )

    if min_score is not None:
        query = query.where(SearchRecord.total_score >= min_score)
    if has_contact is True:
        query = query.where(
            or_(
                SearchRecord.auto_phone.isnot(None),
                SearchRecord.auto_email.isnot(None),
                SearchRecord.manual_contact_phone.isnot(None),
                SearchRecord.manual_contact_email.isnot(None),
            )
        )
    if has_contact is False:
        query = query.where(
            SearchRecord.auto_phone.is_(None),
            SearchRecord.auto_email.is_(None),
            SearchRecord.manual_contact_phone.is_(None),
            SearchRecord.manual_contact_email.is_(None),
        )
    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(
            or_(
                SearchRecord.business_name.ilike(pattern),
                SearchRecord.location.ilike(pattern),
                SearchRecord.category.ilike(pattern),
                SearchRecord.website_url.ilike(pattern),
                SearchRecord.auto_email.ilike(pattern),
                SearchRecord.manual_contact_email.ilike(pattern),
            )
        )

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    rows = (await db.execute(query.limit(limit).offset(offset))).scalars().all()

    search_ids = [row.id for row in rows]
    linked_jobs: dict[int, AuditJob] = {}
    if search_ids:
        jobs = (
            await db.execute(
                select(AuditJob)
                .where(AuditJob.search_id.in_(search_ids))
                .order_by(desc(AuditJob.created_at))
            )
        ).scalars().all()
        for job in jobs:
            if job.search_id not in linked_jobs:
                linked_jobs[job.search_id] = job

    return JSONResponse(
        content={
            "total": total,
            "limit": limit,
            "offset": offset,
            "searches": [
                {
                    **_serialize_search(row),
                    "linked_audit_job": _serialize_audit_job(linked_jobs[row.id]) if row.id in linked_jobs else None,
                }
                for row in rows
            ],
        }
    )


@router.get("/admin/anonymous-searches/{search_id}")
async def admin_anonymous_search_detail(
    search_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await _require_admin_user(request, db)

    search_row = await crud.get_search_by_id(db, search_id)
    if not search_row or search_row.user_id is not None:
        raise HTTPException(404, "Anonymous search not found.")

    lead = await crud.get_lead_by_id(db, search_row.legacy_lead_id) if search_row.legacy_lead_id else None
    audit_job = (
        await db.execute(
            select(AuditJob)
            .where(AuditJob.search_id == search_row.id)
            .order_by(desc(AuditJob.created_at))
            .limit(1)
        )
    ).scalar_one_or_none()
    client = await crud.get_client_by_id(db, audit_job.legacy_client_id) if audit_job and audit_job.legacy_client_id else None

    return JSONResponse(
        content={
            "search": _serialize_search(search_row),
            "audit_json": _json_safe(search_row.audit_json or {}),
            "legacy_lead": _json_safe({**lead.to_dict(), "audit_json": lead.audit_json}) if lead else None,
            "linked_audit_job": _serialize_audit_job(audit_job) if audit_job else None,
            "audit_client": _serialize_client(client) if client else None,
        }
    )


@router.get("/admin/users")
async def admin_users(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    search: Optional[str] = None,
    has_paid: Optional[bool] = None,
    provider: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    await _require_admin_user(request, db)

    search_counts = (
        select(
            SearchRecord.user_id.label("user_id"),
            func.count(SearchRecord.id).label("search_count"),
            func.max(SearchRecord.created_at).label("latest_search_at"),
        )
        .where(SearchRecord.user_id.isnot(None))
        .group_by(SearchRecord.user_id)
        .subquery()
    )
    audit_counts = (
        select(
            AuditJob.user_id.label("user_id"),
            func.count(AuditJob.id).label("audit_count"),
        )
        .where(AuditJob.user_id.isnot(None))
        .group_by(AuditJob.user_id)
        .subquery()
    )

    query = (
        select(
            UserAccount,
            func.coalesce(search_counts.c.search_count, 0).label("search_count"),
            func.coalesce(audit_counts.c.audit_count, 0).label("audit_count"),
            search_counts.c.latest_search_at,
        )
        .outerjoin(search_counts, search_counts.c.user_id == UserAccount.id)
        .outerjoin(audit_counts, audit_counts.c.user_id == UserAccount.id)
        .order_by(desc(UserAccount.created_at))
    )

    if provider:
        query = query.where(UserAccount.auth_provider == provider)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(
            or_(
                UserAccount.email.ilike(pattern),
                UserAccount.name.ilike(pattern),
            )
        )
    if has_paid is True:
        query = query.where(func.coalesce(audit_counts.c.audit_count, 0) > 0)
    if has_paid is False:
        query = query.where(func.coalesce(audit_counts.c.audit_count, 0) == 0)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    rows = (await db.execute(query.limit(limit).offset(offset))).all()

    return JSONResponse(
        content={
            "total": total,
            "limit": limit,
            "offset": offset,
            "users": [
                {
                    **_serialize_user_account(user),
                    "search_count": int(search_count or 0),
                    "audit_count": int(audit_count or 0),
                    "latest_search_at": latest_search_at.isoformat() if latest_search_at else None,
                }
                for user, search_count, audit_count, latest_search_at in rows
            ],
        }
    )


@router.get("/admin/users/{user_id}")
async def admin_user_detail(
    user_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await _require_admin_user(request, db)

    user = (
        await db.execute(select(UserAccount).where(UserAccount.id == user_id))
    ).scalar_one_or_none()
    if not user:
        raise HTTPException(404, "Registered user not found.")

    searches = await crud.get_recent_searches_for_user(db, user.id, limit=12)
    audit_jobs = await crud.get_recent_audit_jobs_for_user(db, user.id, limit=12)
    activities = (
        await db.execute(
            select(UserActivityLog)
            .where(UserActivityLog.user_id == user.id)
            .order_by(desc(UserActivityLog.created_at))
            .limit(20)
        )
    ).scalars().all()
    legacy_client = await crud.get_client_by_email(db, user.email)
    jobs_by_search = {
        job.search_id: job
        for job in audit_jobs
        if job.search_id is not None
    }

    return JSONResponse(
        content={
            "user": _serialize_user_account(user),
            "legacy_client": _serialize_client(legacy_client) if legacy_client else None,
            "searches": [
                {
                    **_serialize_search(search_row),
                    "audit_json": _json_safe(search_row.audit_json or {}),
                    "linked_audit_job": _serialize_audit_job(jobs_by_search[search_row.id]) if search_row.id in jobs_by_search else None,
                }
                for search_row in searches
            ],
            "audit_jobs": [_serialize_audit_job(job) for job in audit_jobs],
            "activity": [_json_safe(activity.to_dict()) for activity in activities],
        }
    )


@router.get("/admin/audits")
async def admin_audits(
    request: Request,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    await _require_admin_user(request, db)

    clients = (
        await db.execute(
            select(AuditClient)
            .where(AuditClient.paid_at.isnot(None))
            .order_by(desc(AuditClient.paid_at))
        )
    ).scalars().all()

    rows = []
    now = datetime.now(timezone.utc)
    for client in clients:
        if status and client.audit_status != status:
            continue

        lead, detailed = await _ensure_audit_workspace(db, client)
        paid_search = await _get_latest_paid_search_for_client(db, client)
        reference_time = client.paid_at or client.created_at or now
        open_days = max((now - reference_time).days, 0)

        rows.append(
            {
                "client": _serialize_client(client),
                "lead": _json_safe(lead.to_dict()) if lead else (_search_as_lead_like(paid_search) if paid_search else None),
                "report_approved": detailed.report_approved,
                "last_edited_at": detailed.last_edited_at.isoformat() if detailed.last_edited_at else None,
                "open_days": open_days,
            }
        )

    rows.sort(
        key=lambda item: (
            AUDIT_SORT_ORDER.get(item["client"]["audit_status"], 99),
            item["client"]["paid_at"] or "",
        )
    )

    return JSONResponse(content={"audits": rows})


@router.get("/admin/audits/{client_id}")
async def admin_audit_detail(
    client_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await _require_admin_user(request, db)

    client = await crud.get_client_by_id(db, client_id)
    if not client:
        raise HTTPException(404, "Paid audit client not found.")

    lead, detailed = await _ensure_audit_workspace(db, client)
    paid_search = await _get_latest_paid_search_for_client(db, client)

    return JSONResponse(
        content={
            "client": _serialize_client(client),
            "lead": _json_safe({**lead.to_dict(), "audit_json": lead.audit_json}) if lead else (_search_as_lead_like(paid_search) if paid_search else None),
            "detailed_audit": _serialize_detailed_audit(detailed),
        }
    )


@router.patch("/admin/audits/{client_id}")
async def admin_update_audit(
    client_id: int,
    req: AuditWorkspaceUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    admin = await _require_admin_user(request, db)

    client = await crud.get_client_by_id(db, client_id)
    if not client:
        raise HTTPException(404, "Paid audit client not found.")

    _, detailed = await _ensure_audit_workspace(db, client)

    if req.audit_status is not None:
        if req.audit_status not in AUDIT_STATUSES:
            raise HTTPException(400, "Invalid audit status.")
        client.audit_status = req.audit_status
        now = datetime.now(timezone.utc)
        if req.audit_status == "in_progress" and not client.audit_started_at:
            client.audit_started_at = now
        elif req.audit_status == "completed" and not client.audit_completed_at:
            client.audit_completed_at = now
        elif req.audit_status == "delivered" and not client.report_delivered_at:
            client.report_delivered_at = now
            client.report_ready_sent_at = now

    if req.analyst_notes is not None:
        detailed.analyst_notes = req.analyst_notes
    if req.ai_synthesis_json is not None:
        detailed.ai_synthesis_json = req.ai_synthesis_json
    if req.instagram_manual is not None:
        detailed.instagram_manual = req.instagram_manual
    if req.facebook_manual is not None:
        detailed.facebook_manual = req.facebook_manual
    if req.linkedin_manual is not None:
        detailed.linkedin_manual = req.linkedin_manual

    for item in req.overrides:
        col = _override_column_for_section(item.section)
        if not col:
            continue
        current_overrides = getattr(detailed, col) or {}
        current_overrides[item.field_name] = {
            "original_value": item.original_value,
            "override_value": item.override_value,
            "reason": item.reason,
            "overridden_by": admin.name,
            "overridden_at": datetime.now(timezone.utc).isoformat(),
        }
        setattr(detailed, col, current_overrides)

    if any([req.analyst_notes is not None, req.ai_synthesis_json is not None, req.instagram_manual is not None, req.facebook_manual is not None, req.linkedin_manual is not None, req.overrides]):
        detailed.analyst_name = admin.name

    detailed.last_edited_by = admin.name
    detailed.last_edited_at = datetime.now(timezone.utc)
    detailed.updated_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(client)
    await db.refresh(detailed)

    return JSONResponse(
        content={
            "success": True,
            "client": _serialize_client(client),
            "detailed_audit": _serialize_detailed_audit(detailed),
        }
    )


@router.post("/admin/audits/{client_id}/approve")
async def admin_approve_audit(
    client_id: int,
    req: ApproveAuditRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    admin = await _require_admin_user(request, db, allowed_roles=APPROVER_ROLES)

    client = await crud.get_client_by_id(db, client_id)
    if not client:
        raise HTTPException(404, "Paid audit client not found.")

    _, detailed = await _ensure_audit_workspace(db, client)
    detailed.report_approved = True
    detailed.approved_by = admin.name
    detailed.approved_at = datetime.now(timezone.utc)
    detailed.last_edited_by = admin.name
    detailed.last_edited_at = datetime.now(timezone.utc)
    if req.report_pdf_path is not None:
        detailed.report_pdf_path = req.report_pdf_path

    client.audit_status = "completed"
    if not client.audit_completed_at:
        client.audit_completed_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(client)
    await db.refresh(detailed)

    return JSONResponse(
        content={
            "success": True,
            "client": _serialize_client(client),
            "detailed_audit": _serialize_detailed_audit(detailed),
        }
    )


@router.get("/admin/team")
async def admin_team(request: Request, db: AsyncSession = Depends(get_db)):
    await _require_admin_user(request, db)

    admins = (
        await db.execute(select(AdminUser).order_by(desc(AdminUser.created_at)))
    ).scalars().all()
    return JSONResponse(content={"admins": [_json_safe(user.to_dict()) for user in admins]})


@router.post("/admin/team")
async def admin_create_team_member(
    req: CreateAdminRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await _require_admin_user(request, db, allowed_roles={"super_admin"})

    if req.role not in {"super_admin", "manager", "analyst"}:
        raise HTTPException(400, "Invalid admin role.")
    if len(req.password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters.")

    existing = (
        await db.execute(select(AdminUser).where(func.lower(AdminUser.email) == req.email.lower()))
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(400, "An admin account with this email already exists.")

    user = await crud.create_admin_user(
        db,
        name=req.name.strip(),
        email=req.email.lower(),
        password_hash=hash_password(req.password),
        role=req.role,
    )
    return JSONResponse(content={"success": True, "admin": _json_safe(user.to_dict())})


@router.patch("/admin/team/{admin_id}")
async def admin_update_team_member(
    admin_id: int,
    req: UpdateAdminRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    current_admin = await _require_admin_user(request, db, allowed_roles={"super_admin"})

    admin = await crud.get_admin_by_id(db, admin_id)
    if not admin:
        raise HTTPException(404, "Admin account not found.")

    if req.role is not None:
        if req.role not in {"super_admin", "manager", "analyst"}:
            raise HTTPException(400, "Invalid admin role.")
        admin.role = req.role

    if req.is_active is not None:
        if admin.id == current_admin.id and req.is_active is False:
            raise HTTPException(400, "You cannot deactivate your own account.")
        admin.is_active = req.is_active

    await db.flush()
    await db.refresh(admin)

    return JSONResponse(content={"success": True, "admin": _json_safe(admin.to_dict())})
