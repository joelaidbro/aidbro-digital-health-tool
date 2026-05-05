from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import crud
from database.models import AuditClient, AuditJob, Lead, SearchRecord, UserAccount


async def get_dashboard_aggregates(
    db: AsyncSession,
    *,
    activity_alert_window_hours: int,
    activity_alert_threshold: int,
) -> dict:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)
    activity_window_start = now - timedelta(hours=activity_alert_window_hours)

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
        threshold=activity_alert_threshold,
        limit=6,
    )
    account_alerts = await crud.get_high_activity_user_rows(
        db,
        since=activity_window_start,
        threshold=activity_alert_threshold,
        limit=6,
    )

    return {
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
        "alert_window_hours": activity_alert_window_hours,
        "alert_threshold": activity_alert_threshold,
    }


async def get_filtered_leads(
    db: AsyncSession,
    *,
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    min_score: Optional[int] = None,
    has_contact: Optional[bool] = None,
    search: Optional[str] = None,
) -> tuple[int, list[Lead]]:
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
    return total, rows


async def get_audit_queue(db: AsyncSession) -> list[AuditClient]:
    return (
        await db.execute(
            select(AuditClient)
            .where(AuditClient.paid_at.isnot(None))
            .order_by(desc(AuditClient.paid_at))
        )
    ).scalars().all()


async def get_user_analytics(
    db: AsyncSession,
    *,
    limit: int = 50,
    offset: int = 0,
    search: Optional[str] = None,
    has_paid: Optional[bool] = None,
    provider: Optional[str] = None,
) -> tuple[int, list]:
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
    return total, rows
