"""
Portal Routes
=============
GET  /api/portal/status       — Audit pipeline status for client
GET  /api/portal/report       — Full report data when ready
GET  /api/portal/report/pdf   — Download final PDF report
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from database import crud
from utils.auth_utils import decode_token

router = APIRouter()


def _require_paid_client(request: Request) -> str:
    """Extract email from JWT and verify it's a paid client."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, "Not authenticated.")
    payload = decode_token(auth[7:])
    if not payload or payload.get("role") != "client":
        raise HTTPException(401, "Client access required.")
    return payload.get("sub")


@router.get("/portal/history")
async def get_portal_history(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Returns the logged-in user's recent searches and paid audit jobs."""
    email = _require_paid_client(request)
    user = await crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(404, "User account not found.")

    searches = await crud.get_recent_searches_for_user(db, user.id, limit=12)
    audit_jobs = await crud.get_recent_audit_jobs_for_user(db, user.id, limit=12)
    jobs_by_search = {
        job.search_id: job
        for job in audit_jobs
        if job.search_id is not None
    }

    return JSONResponse(content={
        "searches": [
            {
                **search.to_dict(),
                "linked_audit_job": jobs_by_search.get(search.id).to_dict() if jobs_by_search.get(search.id) else None,
            }
            for search in searches
        ],
        "audit_jobs": [job.to_dict() for job in audit_jobs],
    })


@router.get("/portal/searches/{search_id}")
async def get_saved_search_detail(
    search_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Returns the full stored audit snapshot for one saved user search."""
    email = _require_paid_client(request)
    user = await crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(404, "User account not found.")

    search = await crud.get_search_by_id(db, search_id)
    if not search:
        raise HTTPException(404, "Saved search not found.")
    if search.user_id != user.id:
        raise HTTPException(403, "You do not have access to this saved search.")

    return JSONResponse(content={
        "search": search.to_dict(),
        "audit": search.audit_json or {},
    })


# ── Audit status pipeline steps ───────────────────────────────────────────────
STATUS_STEPS = {
    "unsubscribed": 0,
    "pending":      2,
    "in_progress":  3,
    "review":       5,
    "completed":    6,
    "delivered":    7,
}

STATUS_LABELS = {
    "unsubscribed": "Payment not received",
    "pending":      "Payment confirmed — audit will begin shortly",
    "in_progress":  "Our team is collecting and analyzing your data",
    "review":       "Report is being reviewed by our team",
    "completed":    "Your report is ready and being prepared for delivery",
    "delivered":    "Your report is ready to download",
}

ALL_STEPS = [
    {"step": 1, "label": "Payment Confirmed",      "status_key": "pending"},
    {"step": 2, "label": "Audit Started",           "status_key": "pending"},
    {"step": 3, "label": "Data Collection",         "status_key": "in_progress"},
    {"step": 4, "label": "Manual Analysis",         "status_key": "in_progress"},
    {"step": 5, "label": "Report Generation",       "status_key": "review"},
    {"step": 6, "label": "Quality Review",          "status_key": "completed"},
    {"step": 7, "label": "Report Ready",            "status_key": "delivered"},
]


@router.get("/portal/status")
async def get_portal_status(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Returns audit pipeline status with step indicators."""
    email = _require_paid_client(request)

    client_obj = await crud.get_client_by_email(db, email)
    if not client_obj:
        raise HTTPException(404, "Account not found.")

    current_step_num = STATUS_STEPS.get(client_obj.audit_status or "unsubscribed", 0)
    has_paid         = client_obj.paid_at is not None

    steps_with_state = []
    for s in ALL_STEPS:
        step_num = s["step"]
        if step_num <= current_step_num:
            state = "complete"
        elif step_num == current_step_num + 1:
            state = "active"
        else:
            state = "pending"
        steps_with_state.append({**s, "state": state})

    # Fetch detailed audit if exists
    detailed = await crud.get_detailed_audit_by_client(db, client_obj.id)
    report_ready = (
        detailed is not None
        and detailed.report_approved
    ) if detailed else False

    return JSONResponse(content={
        "has_paid":       has_paid,
        "audit_status":   client_obj.audit_status,
        "status_label":   STATUS_LABELS.get(client_obj.audit_status, ""),
        "steps":          steps_with_state,
        "current_step":   current_step_num,
        "report_ready":   report_ready,
        "access_until":   client_obj.access_expires_at.isoformat()
                          if client_obj.access_expires_at else None,
        "started_at":     client_obj.audit_started_at.isoformat()
                          if client_obj.audit_started_at else None,
        "completed_at":   client_obj.audit_completed_at.isoformat()
                          if client_obj.audit_completed_at else None,
    })


@router.get("/portal/report")
async def get_report(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the full detailed audit report data.
    Only accessible when audit_status is 'completed' or 'delivered'.
    """
    email = _require_paid_client(request)

    client_obj = await crud.get_client_by_email(db, email)
    if not client_obj:
        raise HTTPException(404, "Account not found.")
    if not client_obj.paid_at:
        raise HTTPException(403, "Report access requires payment.")
    if client_obj.audit_status not in ("completed", "delivered"):
        raise HTTPException(
            403,
            f"Report not ready yet. Current status: {client_obj.audit_status}"
        )

    detailed = await crud.get_detailed_audit_by_client(db, client_obj.id)
    if not detailed or not detailed.report_approved:
        raise HTTPException(403, "Report is still being reviewed.")

    # Mark as delivered if not already
    if client_obj.audit_status == "completed":
        await crud.update_audit_status(db, client_obj.id, "delivered")

    return JSONResponse(content={
        "basic_audit":    detailed.basic_audit_json,
        "seo_audit":      detailed.seo_crawler_json,
        "competitors":    detailed.competitors_json,
        "keywords":       detailed.keywords_json,
        "local_seo":      detailed.local_seo_json,
        "social_report": {
            "instagram": detailed.instagram_manual,
            "facebook":  detailed.facebook_manual,
            "linkedin":  detailed.linkedin_manual,
        },
        "ai_synthesis":   detailed.ai_synthesis_json,
        "analyst_notes":  detailed.analyst_notes,
        "approved_at":    detailed.approved_at.isoformat()
                          if detailed.approved_at else None,
    })


@router.get("/portal/report/pdf")
async def download_report_pdf(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Download the approved PDF report."""
    email = _require_paid_client(request)

    client_obj = await crud.get_client_by_email(db, email)
    if not client_obj or not client_obj.paid_at:
        raise HTTPException(403, "Access denied.")

    detailed = await crud.get_detailed_audit_by_client(db, client_obj.id)
    if not detailed or not detailed.report_approved or not detailed.report_pdf_path:
        raise HTTPException(404, "PDF report not available yet.")

    return FileResponse(
        detailed.report_pdf_path,
        media_type="application/pdf",
        filename=f"aidbro_detailed_report.pdf",
    )
