from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from database import crud

router = APIRouter()


class ContactCaptureRequest(BaseModel):
    lead_id: int
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None


class LeadStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None
    assigned_to: Optional[str] = None


@router.patch("/leads/{lead_id}/contact")
async def capture_contact(
    lead_id: int,
    req: ContactCaptureRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Called when user fills the optional contact form after seeing results.
    Updates the existing lead record with their contact info.
    """
    # Validate at least one field is provided
    if not any([req.contact_name, req.contact_phone, req.contact_email]):
        raise HTTPException(
            status_code=400,
            detail="At least one contact field (name, phone, or email) is required"
        )

    lead = await crud.update_lead_contact(
        db,
        lead_id=lead_id,
        contact_name=req.contact_name,
        contact_phone=req.contact_phone,
        contact_email=req.contact_email,
    )

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # TODO (Phase 2B): Trigger WhatsApp notification to Aidbro team here
    # await notify_team_new_contact(lead)

    return JSONResponse(content={
        "success": True,
        "message": "Contact info saved. Our team will reach out shortly.",
        "lead_id": lead.id,
    })


@router.get("/leads/stats")
async def get_leads_stats(db: AsyncSession = Depends(get_db)):
    """
    Dashboard stats for admin panel.
    Protected by admin auth in Phase 2B — open for now in development.
    """
    stats = await crud.get_leads_stats(db)
    return JSONResponse(content=stats)


@router.get("/leads")
async def get_leads(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    min_score: Optional[int] = None,
    has_contact: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Fetch leads for admin CRM table.
    Protected by admin auth in Phase 2B — open in development.
    """
    leads, total = await crud.get_all_leads(
        db,
        limit=limit,
        offset=offset,
        status_filter=status,
        min_score=min_score,
        has_contact=has_contact,
    )

    return JSONResponse(content={
        "total": total,
        "limit": limit,
        "offset": offset,
        "leads": [lead.to_dict() for lead in leads],
    })


@router.get("/leads/{lead_id}")
async def get_lead(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Fetch a single lead by ID."""
    lead = await crud.get_lead_by_id(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    return JSONResponse(content={
        **lead.to_dict(),
        "audit_json": lead.audit_json,  # Full audit data included here
    })


@router.patch("/leads/{lead_id}/status")
async def update_lead_status(
    lead_id: int,
    req: LeadStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update CRM status of a lead — called from admin panel."""
    valid_statuses = [
        "new", "contacted", "demo_done", "stage4_paid",
        "service_signed", "not_interested", "follow_up"
    ]
    if req.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )

    lead = await crud.update_lead_status(
        db,
        lead_id=lead_id,
        status=req.status,
        notes=req.notes,
        assigned_to=req.assigned_to,
    )

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    return JSONResponse(content={"success": True, "lead": lead.to_dict()})
