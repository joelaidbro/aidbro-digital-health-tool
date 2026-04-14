import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
import io

from services.google_places import search_business
from services.pagespeed import analyze_website
from services.social_check import check_social_presence
from services.scorer import calculate_score
from services.ai_writer import generate_insights
from services.pdf_generator import generate_pdf

router = APIRouter()


class AuditRequest(BaseModel):
    business_name:  str
    location:       str
    category:       Optional[str] = "General Business"
    website_url:    Optional[str] = ""
    instagram_url:  Optional[str] = ""
    facebook_url:   Optional[str] = ""
    linkedin_url:   Optional[str] = ""


@router.post("/audit")
async def run_audit(req: AuditRequest):
    if not req.business_name.strip():
        raise HTTPException(400, "Business name is required")
    if not req.location.strip():
        raise HTTPException(400, "Location is required")

    # ── Step 1: Google Business data ──────────────────────────────────────────
    google_data = await search_business(req.business_name, req.location)

    # Website URL — prefer manually provided, fallback to Google listing
    website_url = req.website_url.strip() or google_data.get("website", "")

    # Collect manually provided social handles
    manual_socials = {
        "instagram_url": req.instagram_url.strip() if req.instagram_url else "",
        "facebook_url":  req.facebook_url.strip()  if req.facebook_url  else "",
        "linkedin_url":  req.linkedin_url.strip()  if req.linkedin_url  else "",
    }

    # ── Step 2: PageSpeed + Social in parallel ─────────────────────────────
    pagespeed_data, social_data = await asyncio.gather(
        analyze_website(website_url),
        check_social_presence(website_url, google_data, manual_socials),
    )

    # ── Step 3: Score ─────────────────────────────────────────────────────
    score_data = calculate_score(
        google_data,
        pagespeed_data,
        social_data,
        category=req.category or "General Business",
    )

    # ── Step 4: AI insights ───────────────────────────────────────────────
    ai_insights = generate_insights(
        req.business_name, req.location, score_data, google_data
    )

    return JSONResponse(content={
        "business": {
            "name":          google_data.get("name", req.business_name),
            "location":      req.location,
            "category":      req.category,
            "address":       google_data.get("address", ""),
            "phone":         google_data.get("phone", ""),
            "website":       website_url,
            "rating":        google_data.get("rating", 0),
            "total_reviews": google_data.get("total_reviews", 0),
            "maps_url":      google_data.get("maps_url", ""),
            "is_mocked":     google_data.get("mocked", False),
        },
        "score":    score_data,
        "pagespeed": pagespeed_data,
        "social":   social_data,
        "insights": ai_insights,
    })


@router.post("/audit/pdf")
async def generate_report_pdf(req: AuditRequest):
    if not req.business_name.strip():
        raise HTTPException(400, "Business name is required")

    google_data = await search_business(req.business_name, req.location)
    website_url = req.website_url.strip() or google_data.get("website", "")

    manual_socials = {
        "instagram_url": req.instagram_url.strip() if req.instagram_url else "",
        "facebook_url":  req.facebook_url.strip()  if req.facebook_url  else "",
        "linkedin_url":  req.linkedin_url.strip()  if req.linkedin_url  else "",
    }

    pagespeed_data, social_data = await asyncio.gather(
        analyze_website(website_url),
        check_social_presence(website_url, google_data, manual_socials),
    )

    score_data  = calculate_score(
        google_data, pagespeed_data, social_data,
        category=req.category or "General Business"
    )
    ai_insights = generate_insights(
        req.business_name, req.location, score_data, google_data
    )

    pdf_bytes = generate_pdf(
        business_name=req.business_name,
        location=req.location,
        score_data=score_data,
        google_data=google_data,
        pagespeed_data=pagespeed_data,
        ai_insights=ai_insights,
    )

    filename = f"aidbro_health_{req.business_name.replace(' ', '_')}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/health")
def health_check():
    return {"status": "ok"}