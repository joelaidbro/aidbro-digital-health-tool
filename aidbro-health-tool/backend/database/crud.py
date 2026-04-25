"""
CRUD Operations — Aidbro Digital Health Tool
=============================================
All database read/write functions used across routes.
Every function takes an AsyncSession as first argument.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, update, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    Lead,
    AuditClient,
    DetailedAudit,
    AdminUser,
    UserAccount,
    SearchRecord,
    PaymentOrder,
    AuditJob,
    UserActivityLog,
)


# ══════════════════════════════════════════════════════════════════════════════
# LEADS
# ══════════════════════════════════════════════════════════════════════════════

async def create_lead(db: AsyncSession, data: dict) -> Lead:
    """
    Create a new lead record from a free tool submission.
    Called silently on every audit — user is not aware of this.
    """
    lead = Lead(
        business_name=data.get("business_name", ""),
        location=data.get("location", ""),
        category=data.get("category"),
        website_url=data.get("website_url"),
        instagram_url=data.get("instagram_url"),
        facebook_url=data.get("facebook_url"),
        linkedin_url=data.get("linkedin_url"),
        contact_name=data.get("contact_name"),
        contact_phone=data.get("contact_phone"),
        contact_email=data.get("contact_email"),
        contact_captured_at=data.get("contact_captured_at"),
        total_score=data.get("total_score"),
        grade=data.get("grade"),
        score_label=data.get("score_label"),
        is_mocked=data.get("is_mocked", False),
        audit_json=data.get("audit_json"),
        ip_address=data.get("ip_address"),
        user_agent=data.get("user_agent"),
        utm_source=data.get("utm_source"),
        utm_medium=data.get("utm_medium"),
        utm_campaign=data.get("utm_campaign"),
        status="new",
    )
    db.add(lead)
    await db.flush()   # flush to get the id without committing yet
    await db.refresh(lead)
    return lead


async def get_lead_by_id(db: AsyncSession, lead_id: int) -> Optional[Lead]:
    """Fetch a single lead by its ID."""
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    return result.scalar_one_or_none()


async def get_latest_lead_by_contact_email(
    db: AsyncSession,
    email: str,
) -> Optional[Lead]:
    """Find the most recent lead that captured the given contact email."""
    result = await db.execute(
        select(Lead)
        .where(func.lower(Lead.contact_email) == email.lower())
        .order_by(desc(Lead.created_at))
        .limit(1)
    )
    return result.scalar_one_or_none()


async def update_lead_contact(
    db: AsyncSession,
    lead_id: int,
    contact_name: Optional[str],
    contact_phone: Optional[str],
    contact_email: Optional[str],
) -> Optional[Lead]:
    """
    Add optional contact info to an existing lead.
    Called when the user fills the ContactCapture form after seeing results.
    """
    lead = await get_lead_by_id(db, lead_id)
    if not lead:
        return None

    if contact_name:
        lead.contact_name = contact_name
    if contact_phone:
        lead.contact_phone = contact_phone
    if contact_email:
        lead.contact_email = contact_email

    lead.contact_captured_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(lead)
    return lead


async def update_lead_status(
    db: AsyncSession,
    lead_id: int,
    status: str,
    notes: Optional[str] = None,
    assigned_to: Optional[str] = None,
) -> Optional[Lead]:
    """Update the CRM status of a lead — called from admin panel."""
    lead = await get_lead_by_id(db, lead_id)
    if not lead:
        return None

    lead.status = status
    if notes is not None:
        lead.notes = notes
    if assigned_to is not None:
        lead.assigned_to = assigned_to

    await db.flush()
    await db.refresh(lead)
    return lead


async def get_all_leads(
    db: AsyncSession,
    limit: int = 50,
    offset: int = 0,
    status_filter: Optional[str] = None,
    min_score: Optional[int] = None,
    has_contact: Optional[bool] = None,
) -> tuple[list[Lead], int]:
    """
    Fetch leads for the admin panel CRM table.
    Returns (leads_list, total_count).
    """
    query = select(Lead).order_by(desc(Lead.created_at))

    if status_filter:
        query = query.where(Lead.status == status_filter)
    if min_score is not None:
        query = query.where(Lead.total_score >= min_score)
    if has_contact is True:
        query = query.where(Lead.contact_phone.isnot(None))
    if has_contact is False:
        query = query.where(Lead.contact_phone.is_(None))

    # Total count (for pagination)
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    # Paginated results
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    leads = result.scalars().all()

    return list(leads), total


async def get_leads_stats(db: AsyncSession) -> dict:
    """
    Dashboard stats for admin panel.
    Returns counts by status + average score + today's count.
    """
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    total = (await db.execute(select(func.count(Lead.id)))).scalar_one()
    today = (
        await db.execute(
            select(func.count(Lead.id)).where(Lead.created_at >= today_start)
        )
    ).scalar_one()
    avg_score = (
        await db.execute(
            select(func.avg(Lead.total_score)).where(Lead.total_score.isnot(None))
        )
    ).scalar_one()
    with_contact = (
        await db.execute(
            select(func.count(Lead.id)).where(Lead.contact_phone.isnot(None))
        )
    ).scalar_one()

    # Count by status
    status_counts = {}
    for status in ["new", "contacted", "demo_done", "stage4_paid", "service_signed", "not_interested"]:
        count = (
            await db.execute(
                select(func.count(Lead.id)).where(Lead.status == status)
            )
        ).scalar_one()
        status_counts[status] = count

    return {
        "total": total,
        "today": today,
        "avg_score": round(float(avg_score), 1) if avg_score else 0,
        "with_contact": with_contact,
        "by_status": status_counts,
    }


# ══════════════════════════════════════════════════════════════════════════════
# AUDIT CLIENTS (Stage 4 paying customers)
# ══════════════════════════════════════════════════════════════════════════════

async def create_audit_client(
    db: AsyncSession,
    email: str,
    password_hash: str,
    payment_id: str,
    order_id: str,
    amount_paid: float,
    lead_id: Optional[int] = None,
    plan_type: str = "basic_audit",
) -> AuditClient:
    """Create a paying client after successful Razorpay payment."""
    from datetime import timedelta

    client = AuditClient(
        lead_id=lead_id,
        email=email,
        password_hash=password_hash,
        payment_id=payment_id,
        order_id=order_id,
        amount_paid=amount_paid,
        currency="INR",
        paid_at=datetime.now(timezone.utc),
        plan_type=plan_type,
        audit_status="pending",
        # Portal access valid for 90 days
        access_expires_at=datetime.now(timezone.utc) + timedelta(days=90),
    )
    db.add(client)
    await db.flush()
    await db.refresh(client)

    # Update the lead status if linked
    if lead_id:
        await update_lead_status(db, lead_id, "stage4_paid")

    return client


async def get_client_by_email(db: AsyncSession, email: str) -> Optional[AuditClient]:
    result = await db.execute(
        select(AuditClient).where(AuditClient.email == email)
    )
    return result.scalar_one_or_none()


async def get_client_by_id(db: AsyncSession, client_id: int) -> Optional[AuditClient]:
    result = await db.execute(
        select(AuditClient).where(AuditClient.id == client_id)
    )
    return result.scalar_one_or_none()


async def update_audit_status(
    db: AsyncSession, client_id: int, status: str
) -> Optional[AuditClient]:
    """Update audit pipeline status — called by admin panel."""
    client = await get_client_by_id(db, client_id)
    if not client:
        return None

    client.audit_status = status

    now = datetime.now(timezone.utc)
    if status == "in_progress" and not client.audit_started_at:
        client.audit_started_at = now
    elif status == "completed" and not client.audit_completed_at:
        client.audit_completed_at = now
    elif status == "delivered" and not client.report_delivered_at:
        client.report_delivered_at = now
        client.report_ready_sent_at = now

    await db.flush()
    await db.refresh(client)
    return client


# ══════════════════════════════════════════════════════════════════════════════
# DETAILED AUDITS (Stage 4 deep audit data)
# ══════════════════════════════════════════════════════════════════════════════

async def create_detailed_audit(
    db: AsyncSession, client_id: int
) -> DetailedAudit:
    """Initialize an empty detailed audit record when client pays."""
    audit = DetailedAudit(
        client_id=client_id,
        basic_audit_overrides={},
        seo_overrides={},
        competitors_overrides={},
        keywords_overrides={},
        local_seo_overrides={},
    )
    db.add(audit)
    await db.flush()
    await db.refresh(audit)
    return audit


async def get_detailed_audit_by_client(
    db: AsyncSession, client_id: int
) -> Optional[DetailedAudit]:
    result = await db.execute(
        select(DetailedAudit).where(DetailedAudit.client_id == client_id)
    )
    return result.scalar_one_or_none()


async def save_automated_data(
    db: AsyncSession,
    audit_id: int,
    section: str,
    data: dict,
) -> Optional[DetailedAudit]:
    """
    Save automated section data.
    section: 'basic_audit' | 'seo_crawler' | 'competitors' | 'keywords' | 'local_seo'
    """
    result = await db.execute(
        select(DetailedAudit).where(DetailedAudit.id == audit_id)
    )
    audit = result.scalar_one_or_none()
    if not audit:
        return None

    column_map = {
        "basic_audit": "basic_audit_json",
        "seo_crawler": "seo_crawler_json",
        "competitors": "competitors_json",
        "keywords": "keywords_json",
        "local_seo": "local_seo_json",
    }
    col = column_map.get(section)
    if col:
        setattr(audit, col, data)

    audit.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(audit)
    return audit


async def save_override(
    db: AsyncSession,
    audit_id: int,
    section: str,
    field_name: str,
    original_value,
    override_value,
    reason: str,
    overridden_by: str,
) -> Optional[DetailedAudit]:
    """
    Save a manual override for an automated data field.
    Preserves the original value alongside the override for audit trail.
    """
    result = await db.execute(
        select(DetailedAudit).where(DetailedAudit.id == audit_id)
    )
    audit = result.scalar_one_or_none()
    if not audit:
        return None

    override_col_map = {
        "basic_audit": "basic_audit_overrides",
        "seo": "seo_overrides",
        "competitors": "competitors_overrides",
        "keywords": "keywords_overrides",
        "local_seo": "local_seo_overrides",
    }
    col = override_col_map.get(section)
    if not col:
        return None

    current_overrides = getattr(audit, col) or {}
    current_overrides[field_name] = {
        "original_value": original_value,
        "override_value": override_value,
        "reason": reason,
        "overridden_by": overridden_by,
        "overridden_at": datetime.now(timezone.utc).isoformat(),
    }
    setattr(audit, col, current_overrides)

    audit.last_edited_by = overridden_by
    audit.last_edited_at = datetime.now(timezone.utc)
    audit.updated_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(audit)
    return audit


async def save_manual_social_data(
    db: AsyncSession,
    audit_id: int,
    platform: str,
    data: dict,
    analyst_name: str,
) -> Optional[DetailedAudit]:
    """Save analyst-entered social media report for a platform."""
    result = await db.execute(
        select(DetailedAudit).where(DetailedAudit.id == audit_id)
    )
    audit = result.scalar_one_or_none()
    if not audit:
        return None

    col_map = {
        "instagram": "instagram_manual",
        "facebook": "facebook_manual",
        "linkedin": "linkedin_manual",
    }
    col = col_map.get(platform.lower())
    if col:
        setattr(audit, col, data)

    audit.analyst_name = analyst_name
    audit.last_edited_by = analyst_name
    audit.last_edited_at = datetime.now(timezone.utc)
    audit.updated_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(audit)
    return audit


async def approve_report(
    db: AsyncSession,
    audit_id: int,
    approved_by: str,
    report_pdf_path: Optional[str] = None,
) -> Optional[DetailedAudit]:
    """Mark a detailed audit report as approved and ready for client."""
    result = await db.execute(
        select(DetailedAudit).where(DetailedAudit.id == audit_id)
    )
    audit = result.scalar_one_or_none()
    if not audit:
        return None

    audit.report_approved = True
    audit.approved_by = approved_by
    audit.approved_at = datetime.now(timezone.utc)
    if report_pdf_path:
        audit.report_pdf_path = report_pdf_path

    await db.flush()
    await db.refresh(audit)
    return audit


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN USERS
# ══════════════════════════════════════════════════════════════════════════════

async def create_admin_user(
    db: AsyncSession,
    name: str,
    email: str,
    password_hash: str,
    role: str = "analyst",
) -> AdminUser:
    user = AdminUser(
        name=name,
        email=email,
        password_hash=password_hash,
        role=role,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def get_admin_by_email(db: AsyncSession, email: str) -> Optional[AdminUser]:
    result = await db.execute(
        select(AdminUser).where(AdminUser.email == email, AdminUser.is_active == True)
    )
    return result.scalar_one_or_none()


async def get_admin_by_id(db: AsyncSession, admin_id: int) -> Optional[AdminUser]:
    result = await db.execute(
        select(AdminUser).where(AdminUser.id == admin_id)
    )
    return result.scalar_one_or_none()


async def update_admin_last_login(db: AsyncSession, admin_id: int) -> None:
    await db.execute(
        update(AdminUser)
        .where(AdminUser.id == admin_id)
        .values(last_login_at=datetime.now(timezone.utc))
    )


# ══════════════════════════════════════════════════════════════════════════════
# USERS / SEARCHES / ORDERS / AUDIT JOBS (new architecture foundation)
# ══════════════════════════════════════════════════════════════════════════════

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[UserAccount]:
    result = await db.execute(
        select(UserAccount).where(func.lower(UserAccount.email) == email.lower())
    )
    return result.scalar_one_or_none()


async def create_user_account(
    db: AsyncSession,
    email: str,
    password_hash: Optional[str] = None,
    name: Optional[str] = None,
    auth_provider: str = "email",
) -> UserAccount:
    user = UserAccount(
        email=email.lower(),
        password_hash=password_hash,
        name=name,
        auth_provider=auth_provider,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def update_user_last_login(db: AsyncSession, user_id: int) -> None:
    await db.execute(
        update(UserAccount)
        .where(UserAccount.id == user_id)
        .values(last_login_at=datetime.now(timezone.utc))
    )


async def create_user_activity(
    db: AsyncSession,
    user_id: int,
    event_type: str,
    meta_json: Optional[dict] = None,
) -> UserActivityLog:
    activity = UserActivityLog(
        user_id=user_id,
        event_type=event_type,
        meta_json=meta_json or {},
    )
    db.add(activity)
    await db.flush()
    await db.refresh(activity)
    return activity


async def create_search_record(db: AsyncSession, data: dict) -> SearchRecord:
    search = SearchRecord(
        user_id=data.get("user_id"),
        legacy_lead_id=data.get("legacy_lead_id"),
        business_name=data.get("business_name", ""),
        location=data.get("location", ""),
        category=data.get("category"),
        website_url=data.get("website_url"),
        instagram_url=data.get("instagram_url"),
        facebook_url=data.get("facebook_url"),
        linkedin_url=data.get("linkedin_url"),
        youtube_url=data.get("youtube_url"),
        twitter_url=data.get("twitter_url"),
        auto_phone=data.get("auto_phone"),
        auto_email=data.get("auto_email"),
        manual_contact_name=data.get("manual_contact_name"),
        manual_contact_phone=data.get("manual_contact_phone"),
        manual_contact_email=data.get("manual_contact_email"),
        manual_contact_captured_at=data.get("manual_contact_captured_at"),
        total_score=data.get("total_score"),
        grade=data.get("grade"),
        score_label=data.get("score_label"),
        is_mocked=data.get("is_mocked", False),
        source_type=data.get("source_type", "anonymous"),
        status=data.get("status", "new"),
        audit_json=data.get("audit_json"),
        utm_source=data.get("utm_source"),
        utm_medium=data.get("utm_medium"),
        utm_campaign=data.get("utm_campaign"),
        ip_address=data.get("ip_address"),
        user_agent=data.get("user_agent"),
    )
    db.add(search)
    await db.flush()
    await db.refresh(search)
    return search


async def get_search_by_id(db: AsyncSession, search_id: int) -> Optional[SearchRecord]:
    result = await db.execute(select(SearchRecord).where(SearchRecord.id == search_id))
    return result.scalar_one_or_none()


async def get_latest_search_for_user(
    db: AsyncSession,
    user_id: int,
) -> Optional[SearchRecord]:
    result = await db.execute(
        select(SearchRecord)
        .where(SearchRecord.user_id == user_id)
        .order_by(desc(SearchRecord.created_at))
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_recent_searches_for_user(
    db: AsyncSession,
    user_id: int,
    limit: int = 10,
) -> list[SearchRecord]:
    result = await db.execute(
        select(SearchRecord)
        .where(SearchRecord.user_id == user_id)
        .order_by(desc(SearchRecord.created_at))
        .limit(limit)
    )
    return list(result.scalars().all())


async def count_recent_searches_by_ip(
    db: AsyncSession,
    ip_address: str,
    since: datetime,
    anonymous_only: bool = False,
) -> int:
    query = select(func.count(SearchRecord.id)).where(
        SearchRecord.ip_address == ip_address,
        SearchRecord.created_at >= since,
    )
    if anonymous_only:
        query = query.where(SearchRecord.user_id.is_(None))
    result = await db.execute(query)
    return int(result.scalar_one() or 0)


async def get_high_activity_ip_rows(
    db: AsyncSession,
    since: datetime,
    threshold: int,
    limit: int = 10,
) -> list[dict]:
    rows = (
        await db.execute(
            select(
                SearchRecord.ip_address,
                func.count(SearchRecord.id).label("search_count"),
            )
            .where(
                SearchRecord.ip_address.isnot(None),
                SearchRecord.created_at >= since,
            )
            .group_by(SearchRecord.ip_address)
            .having(func.count(SearchRecord.id) >= threshold)
            .order_by(desc(func.count(SearchRecord.id)))
            .limit(limit)
        )
    ).all()
    return [
        {
            "label": ip_address,
            "count": int(search_count or 0),
        }
        for ip_address, search_count in rows
        if ip_address
    ]


async def get_high_activity_user_rows(
    db: AsyncSession,
    since: datetime,
    threshold: int,
    limit: int = 10,
) -> list[dict]:
    rows = (
        await db.execute(
            select(
                UserAccount.email,
                func.count(SearchRecord.id).label("search_count"),
            )
            .join(SearchRecord, SearchRecord.user_id == UserAccount.id)
            .where(SearchRecord.created_at >= since)
            .group_by(UserAccount.email)
            .having(func.count(SearchRecord.id) >= threshold)
            .order_by(desc(func.count(SearchRecord.id)))
            .limit(limit)
        )
    ).all()
    return [
        {
            "label": email,
            "count": int(search_count or 0),
        }
        for email, search_count in rows
        if email
    ]


async def create_payment_order_record(
    db: AsyncSession,
    *,
    user_id: Optional[int],
    search_id: Optional[int],
    legacy_client_id: Optional[int],
    legacy_lead_id: Optional[int],
    razorpay_order_id: str,
    amount: float,
    currency: str = "INR",
    status: str = "created",
    plan_type: str = "basic_audit",
) -> PaymentOrder:
    order = PaymentOrder(
        user_id=user_id,
        search_id=search_id,
        legacy_client_id=legacy_client_id,
        legacy_lead_id=legacy_lead_id,
        razorpay_order_id=razorpay_order_id,
        amount=amount,
        currency=currency,
        status=status,
        plan_type=plan_type,
    )
    db.add(order)
    await db.flush()
    await db.refresh(order)
    return order


async def get_payment_order_by_razorpay_order_id(
    db: AsyncSession,
    razorpay_order_id: str,
) -> Optional[PaymentOrder]:
    result = await db.execute(
        select(PaymentOrder).where(PaymentOrder.razorpay_order_id == razorpay_order_id)
    )
    return result.scalar_one_or_none()


async def get_payment_order_by_payment_id(
    db: AsyncSession,
    razorpay_payment_id: str,
) -> Optional[PaymentOrder]:
    result = await db.execute(
        select(PaymentOrder).where(PaymentOrder.razorpay_payment_id == razorpay_payment_id)
    )
    return result.scalar_one_or_none()


async def create_audit_job_record(
    db: AsyncSession,
    *,
    user_id: Optional[int],
    search_id: Optional[int],
    order_id: Optional[int],
    legacy_client_id: Optional[int],
    legacy_detailed_audit_id: Optional[int],
    audit_status: str = "pending",
    access_expires_at=None,
    report_approved: bool = False,
    report_pdf_path: Optional[str] = None,
) -> AuditJob:
    job = AuditJob(
        user_id=user_id,
        search_id=search_id,
        order_id=order_id,
        legacy_client_id=legacy_client_id,
        legacy_detailed_audit_id=legacy_detailed_audit_id,
        audit_status=audit_status,
        access_expires_at=access_expires_at,
        report_approved=report_approved,
        report_pdf_path=report_pdf_path,
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)
    return job


async def get_audit_job_by_order_id(
    db: AsyncSession,
    order_id: int,
) -> Optional[AuditJob]:
    result = await db.execute(select(AuditJob).where(AuditJob.order_id == order_id))
    return result.scalar_one_or_none()


async def get_recent_audit_jobs_for_user(
    db: AsyncSession,
    user_id: int,
    limit: int = 10,
) -> list[AuditJob]:
    result = await db.execute(
        select(AuditJob)
        .where(AuditJob.user_id == user_id)
        .order_by(desc(AuditJob.created_at))
        .limit(limit)
    )
    return list(result.scalars().all())
