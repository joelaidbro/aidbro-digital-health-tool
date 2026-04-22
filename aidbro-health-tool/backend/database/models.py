"""
Database Models — Aidbro Digital Health Tool
============================================
Tables:
  1. leads          — Every free tool submission
  2. audit_clients  — Stage 4 paying customers
  3. detailed_audits — Stage 4 deep audit data
  4. admin_users    — Aidbro team members
"""

from datetime import datetime
from sqlalchemy import (
    Integer, String, Text, Boolean, DateTime,
    Numeric, ForeignKey, func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.connection import Base


# ══════════════════════════════════════════════════════════════════════════════
# TABLE 1: leads
# Every free tool submission — with or without contact info
# ══════════════════════════════════════════════════════════════════════════════

class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Form inputs ──────────────────────────────────────────────────────────
    business_name: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100))
    website_url: Mapped[str | None] = mapped_column(String(500))
    instagram_url: Mapped[str | None] = mapped_column(String(500))
    facebook_url: Mapped[str | None] = mapped_column(String(500))
    linkedin_url: Mapped[str | None] = mapped_column(String(500))

    # ── Optional contact info (filled after seeing results) ──────────────────
    contact_name: Mapped[str | None] = mapped_column(String(255))
    contact_phone: Mapped[str | None] = mapped_column(String(20))   # WhatsApp number
    contact_email: Mapped[str | None] = mapped_column(String(255))
    contact_captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # ── Audit results snapshot ───────────────────────────────────────────────
    total_score: Mapped[int | None] = mapped_column(Integer)
    grade: Mapped[str | None] = mapped_column(String(1))
    score_label: Mapped[str | None] = mapped_column(String(50))
    is_mocked: Mapped[bool] = mapped_column(Boolean, default=False)

    # ── Full audit JSON (stored for re-generating reports) ───────────────────
    audit_json: Mapped[dict | None] = mapped_column(JSONB)

    # ── CRM tracking ─────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(String(50), default="new")
    # Values: new | contacted | demo_done | stage4_paid |
    #         service_signed | not_interested | follow_up

    notes: Mapped[str | None] = mapped_column(Text)
    assigned_to: Mapped[str | None] = mapped_column(String(100))
    follow_up_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # ── Attribution ───────────────────────────────────────────────────────────
    utm_source: Mapped[str | None] = mapped_column(String(100))
    utm_medium: Mapped[str | None] = mapped_column(String(100))
    utm_campaign: Mapped[str | None] = mapped_column(String(100))
    ip_address: Mapped[str | None] = mapped_column(String(50))
    user_agent: Mapped[str | None] = mapped_column(Text)

    # ── Relationship ──────────────────────────────────────────────────────────
    audit_client: Mapped["AuditClient | None"] = relationship(
        "AuditClient", back_populates="lead", uselist=False
    )

    def __repr__(self):
        return (
            f"<Lead id={self.id} business='{self.business_name}' "
            f"score={self.total_score} status='{self.status}'>"
        )

    def to_dict(self):
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "business_name": self.business_name,
            "location": self.location,
            "category": self.category,
            "website_url": self.website_url,
            "contact_name": self.contact_name,
            "contact_phone": self.contact_phone,
            "contact_email": self.contact_email,
            "total_score": self.total_score,
            "grade": self.grade,
            "score_label": self.score_label,
            "status": self.status,
            "notes": self.notes,
            "assigned_to": self.assigned_to,
            "follow_up_date": self.follow_up_date.isoformat() if self.follow_up_date else None,
            "is_mocked": self.is_mocked,
        }


# ══════════════════════════════════════════════════════════════════════════════
# TABLE 2: audit_clients
# Stage 4 paying customers — auto-created on successful payment
# ══════════════════════════════════════════════════════════════════════════════

class AuditClient(Base):
    __tablename__ = "audit_clients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Lead reference ────────────────────────────────────────────────────────
    lead_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("leads.id"), nullable=True
    )

    # ── Login credentials ─────────────────────────────────────────────────────
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # ── Payment ───────────────────────────────────────────────────────────────
    payment_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    order_id: Mapped[str | None] = mapped_column(String(255))
    amount_paid: Mapped[float | None] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(10), default="INR")
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    plan_type: Mapped[str] = mapped_column(String(50), default="basic_audit")
    # Values: basic_audit | detailed_audit | monthly_subscription

    # ── Audit status ──────────────────────────────────────────────────────────
    audit_status: Mapped[str] = mapped_column(String(50), default="pending")
    # Values: pending | in_progress | review | completed | delivered

    # ── Timestamps ────────────────────────────────────────────────────────────
    audit_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    audit_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    report_delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    access_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # ── Notification tracking ─────────────────────────────────────────────────
    credentials_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    report_ready_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # ── Relationships ──────────────────────────────────────────────────────────
    lead: Mapped["Lead | None"] = relationship("Lead", back_populates="audit_client")
    detailed_audit: Mapped["DetailedAudit | None"] = relationship(
        "DetailedAudit", back_populates="client", uselist=False
    )

    def __repr__(self):
        return (
            f"<AuditClient id={self.id} email='{self.email}' "
            f"status='{self.audit_status}'>"
        )

    def to_dict(self):
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "email": self.email,
            "plan_type": self.plan_type,
            "audit_status": self.audit_status,
            "amount_paid": float(self.amount_paid) if self.amount_paid else None,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "audit_started_at": self.audit_started_at.isoformat() if self.audit_started_at else None,
            "report_delivered_at": self.report_delivered_at.isoformat() if self.report_delivered_at else None,
            "access_expires_at": self.access_expires_at.isoformat() if self.access_expires_at else None,
        }


# ══════════════════════════════════════════════════════════════════════════════
# TABLE 3: detailed_audits
# Stage 4 deep audit data — mix of automated + manual + overrides
# ══════════════════════════════════════════════════════════════════════════════

class DetailedAudit(Base):
    __tablename__ = "detailed_audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("audit_clients.id"), unique=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ── AUTOMATED DATA ────────────────────────────────────────────────────────
    basic_audit_json: Mapped[dict | None] = mapped_column(JSONB)
    seo_crawler_json: Mapped[dict | None] = mapped_column(JSONB)
    competitors_json: Mapped[dict | None] = mapped_column(JSONB)
    keywords_json: Mapped[dict | None] = mapped_column(JSONB)
    local_seo_json: Mapped[dict | None] = mapped_column(JSONB)

    # ── MANUAL OVERRIDES ──────────────────────────────────────────────────────
    # Every automated section has a corresponding override column.
    # Override structure per field:
    # {
    #   "field_name": {
    #     "original_value": <auto value>,
    #     "override_value": <corrected value>,
    #     "reason": "explanation",
    #     "overridden_by": "analyst name",
    #     "overridden_at": "ISO timestamp"
    #   }
    # }
    basic_audit_overrides: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    seo_overrides: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    competitors_overrides: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    keywords_overrides: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    local_seo_overrides: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    # ── MANUAL DATA (analyst-entered) ─────────────────────────────────────────
    instagram_manual: Mapped[dict | None] = mapped_column(JSONB)
    facebook_manual: Mapped[dict | None] = mapped_column(JSONB)
    linkedin_manual: Mapped[dict | None] = mapped_column(JSONB)
    analyst_notes: Mapped[str | None] = mapped_column(Text)
    analyst_name: Mapped[str | None] = mapped_column(String(100))

    # ── AI SYNTHESIS ──────────────────────────────────────────────────────────
    ai_synthesis_json: Mapped[dict | None] = mapped_column(JSONB)

    # ── APPROVAL ──────────────────────────────────────────────────────────────
    report_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_by: Mapped[str | None] = mapped_column(String(100))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    report_pdf_path: Mapped[str | None] = mapped_column(String(500))

    # ── TRACKING ──────────────────────────────────────────────────────────────
    last_edited_by: Mapped[str | None] = mapped_column(String(100))
    last_edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # ── Relationship ──────────────────────────────────────────────────────────
    client: Mapped["AuditClient"] = relationship(
        "AuditClient", back_populates="detailed_audit"
    )

    def __repr__(self):
        return (
            f"<DetailedAudit id={self.id} client_id={self.client_id} "
            f"approved={self.report_approved}>"
        )


# ══════════════════════════════════════════════════════════════════════════════
# TABLE 4: users
# Canonical login identity for every registered or Google-authenticated user
# ══════════════════════════════════════════════════════════════════════════════

class UserAccount(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(255))
    password_hash: Mapped[str | None] = mapped_column(String(255))
    auth_provider: Mapped[str] = mapped_column(String(50), default="email")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    searches: Mapped[list["SearchRecord"]] = relationship("SearchRecord", back_populates="user")
    payment_orders: Mapped[list["PaymentOrder"]] = relationship("PaymentOrder", back_populates="user")
    audit_jobs: Mapped[list["AuditJob"]] = relationship("AuditJob", back_populates="user")
    activity_logs: Mapped[list["UserActivityLog"]] = relationship("UserActivityLog", back_populates="user")

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "auth_provider": self.auth_provider,
            "is_active": self.is_active,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ══════════════════════════════════════════════════════════════════════════════
# TABLE 5: searches
# Every free audit run, whether anonymous or tied to a logged-in user
# ══════════════════════════════════════════════════════════════════════════════

class SearchRecord(Base):
    __tablename__ = "searches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"))
    legacy_lead_id: Mapped[int | None] = mapped_column(Integer)

    business_name: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100))
    website_url: Mapped[str | None] = mapped_column(String(500))
    instagram_url: Mapped[str | None] = mapped_column(String(500))
    facebook_url: Mapped[str | None] = mapped_column(String(500))
    linkedin_url: Mapped[str | None] = mapped_column(String(500))
    youtube_url: Mapped[str | None] = mapped_column(String(500))
    twitter_url: Mapped[str | None] = mapped_column(String(500))

    auto_phone: Mapped[str | None] = mapped_column(String(50))
    auto_email: Mapped[str | None] = mapped_column(String(255))
    manual_contact_name: Mapped[str | None] = mapped_column(String(255))
    manual_contact_phone: Mapped[str | None] = mapped_column(String(50))
    manual_contact_email: Mapped[str | None] = mapped_column(String(255))
    manual_contact_captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    total_score: Mapped[int | None] = mapped_column(Integer)
    grade: Mapped[str | None] = mapped_column(String(1))
    score_label: Mapped[str | None] = mapped_column(String(50))
    is_mocked: Mapped[bool] = mapped_column(Boolean, default=False)
    source_type: Mapped[str] = mapped_column(String(50), default="anonymous")
    status: Mapped[str] = mapped_column(String(50), default="new")

    audit_json: Mapped[dict | None] = mapped_column(JSONB)
    utm_source: Mapped[str | None] = mapped_column(String(100))
    utm_medium: Mapped[str | None] = mapped_column(String(100))
    utm_campaign: Mapped[str | None] = mapped_column(String(100))
    ip_address: Mapped[str | None] = mapped_column(String(50))
    user_agent: Mapped[str | None] = mapped_column(Text)

    user: Mapped["UserAccount | None"] = relationship("UserAccount", back_populates="searches")
    payment_orders: Mapped[list["PaymentOrder"]] = relationship("PaymentOrder", back_populates="search")
    audit_jobs: Mapped[list["AuditJob"]] = relationship("AuditJob", back_populates="search")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "legacy_lead_id": self.legacy_lead_id,
            "business_name": self.business_name,
            "location": self.location,
            "category": self.category,
            "website_url": self.website_url,
            "auto_phone": self.auto_phone,
            "auto_email": self.auto_email,
            "manual_contact_name": self.manual_contact_name,
            "manual_contact_phone": self.manual_contact_phone,
            "manual_contact_email": self.manual_contact_email,
            "total_score": self.total_score,
            "grade": self.grade,
            "score_label": self.score_label,
            "source_type": self.source_type,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ══════════════════════════════════════════════════════════════════════════════
# TABLE 6: payment_orders
# Every order/payment attempt for a specific user search
# ══════════════════════════════════════════════════════════════════════════════

class PaymentOrder(Base):
    __tablename__ = "payment_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"))
    search_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("searches.id"))
    legacy_client_id: Mapped[int | None] = mapped_column(Integer)
    legacy_lead_id: Mapped[int | None] = mapped_column(Integer)

    razorpay_order_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    razorpay_payment_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    amount: Mapped[float | None] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(10), default="INR")
    status: Mapped[str] = mapped_column(String(50), default="created")
    plan_type: Mapped[str] = mapped_column(String(50), default="basic_audit")
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["UserAccount | None"] = relationship("UserAccount", back_populates="payment_orders")
    search: Mapped["SearchRecord | None"] = relationship("SearchRecord", back_populates="payment_orders")
    audit_job: Mapped["AuditJob | None"] = relationship("AuditJob", back_populates="order", uselist=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "search_id": self.search_id,
            "legacy_client_id": self.legacy_client_id,
            "legacy_lead_id": self.legacy_lead_id,
            "razorpay_order_id": self.razorpay_order_id,
            "razorpay_payment_id": self.razorpay_payment_id,
            "amount": float(self.amount) if self.amount is not None else None,
            "currency": self.currency,
            "status": self.status,
            "plan_type": self.plan_type,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ══════════════════════════════════════════════════════════════════════════════
# TABLE 7: audit_jobs
# One paid detailed audit job tied to a search and payment order
# ══════════════════════════════════════════════════════════════════════════════

class AuditJob(Base):
    __tablename__ = "audit_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"))
    search_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("searches.id"))
    order_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("payment_orders.id"), unique=True)
    legacy_client_id: Mapped[int | None] = mapped_column(Integer)
    legacy_detailed_audit_id: Mapped[int | None] = mapped_column(Integer)

    audit_status: Mapped[str] = mapped_column(String(50), default="pending")
    access_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    report_ready_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    report_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    report_pdf_path: Mapped[str | None] = mapped_column(String(500))

    user: Mapped["UserAccount | None"] = relationship("UserAccount", back_populates="audit_jobs")
    search: Mapped["SearchRecord | None"] = relationship("SearchRecord", back_populates="audit_jobs")
    order: Mapped["PaymentOrder | None"] = relationship("PaymentOrder", back_populates="audit_job")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "search_id": self.search_id,
            "order_id": self.order_id,
            "legacy_client_id": self.legacy_client_id,
            "legacy_detailed_audit_id": self.legacy_detailed_audit_id,
            "audit_status": self.audit_status,
            "access_expires_at": self.access_expires_at.isoformat() if self.access_expires_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "report_ready_at": self.report_ready_at.isoformat() if self.report_ready_at else None,
            "report_approved": self.report_approved,
            "report_pdf_path": self.report_pdf_path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ══════════════════════════════════════════════════════════════════════════════
# TABLE 8: user_activity_logs
# Lightweight activity trail for history, support, and admin visibility
# ══════════════════════════════════════════════════════════════════════════════

class UserActivityLog(Base):
    __tablename__ = "user_activity_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    meta_json: Mapped[dict | None] = mapped_column(JSONB)

    user: Mapped["UserAccount"] = relationship("UserAccount", back_populates="activity_logs")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "event_type": self.event_type,
            "meta_json": self.meta_json,
        }


# ══════════════════════════════════════════════════════════════════════════════
# TABLE 9: admin_users
# Aidbro team members who access the admin panel
# ══════════════════════════════════════════════════════════════════════════════

class AdminUser(Base):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    role: Mapped[str] = mapped_column(String(50), default="analyst")
    # Values: super_admin | manager | analyst

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def __repr__(self):
        return f"<AdminUser id={self.id} email='{self.email}' role='{self.role}'>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
        }
