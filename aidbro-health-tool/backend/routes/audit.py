import asyncio
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
import io

from services.google_places import search_business
from services.pagespeed import analyze_website, normalise_url
from services.social_check import check_social_presence
from services.scorer import calculate_score
from services.ai_writer import generate_insights
from services.contact_finder import discover_contact_email
from services.pdf_generator import generate_pdf
from services.seo_crawler import crawl_website
from services.seo_recommendations import generate_seo_recommendations
from services.competitor_analyzer import analyze_competitors
from services.keyword_extractor import extract_keywords
from database.connection import get_db
from database import crud
from sqlalchemy.ext.asyncio import AsyncSession
from utils.auth_utils import decode_token

router = APIRouter()

ANONYMOUS_AUDIT_LIMIT = 2
ANONYMOUS_AUDIT_WINDOW_DAYS = 7


async def _get_request_user(db: AsyncSession, request: Request):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None

    payload = decode_token(auth[7:])
    if not payload or payload.get("role") != "client":
        return None

    email = payload.get("sub", "")
    if not email:
        return None
    return await crud.get_user_by_email(db, email)


class AuditRequest(BaseModel):
    business_name:  str
    location:       str
    category:       Optional[str] = "General Business"
    website_url:    Optional[str] = ""
    instagram_url:  Optional[str] = ""
    facebook_url:   Optional[str] = ""
    linkedin_url:   Optional[str] = ""
    youtube_url:    Optional[str] = ""
    twitter_url:    Optional[str] = ""


@router.post("/audit")
async def run_audit(
    req: AuditRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    if not req.business_name.strip():
        raise HTTPException(400, "Business name is required")
    if not req.location.strip():
        raise HTTPException(400, "Location is required")

    user = await _get_request_user(db, request)
    requester_ip = request.client.host if request.client else None

    if not user and requester_ip:
        window_start = datetime.now(timezone.utc) - timedelta(days=ANONYMOUS_AUDIT_WINDOW_DAYS)
        recent_count = await crud.count_recent_searches_by_ip(
            db,
            requester_ip,
            window_start,
            anonymous_only=True,
        )
        if recent_count >= ANONYMOUS_AUDIT_LIMIT:
            raise HTTPException(
                429,
                (
                    f"You have used the {ANONYMOUS_AUDIT_LIMIT} free audit tries available without login "
                    f"in the last {ANONYMOUS_AUDIT_WINDOW_DAYS} days. Please log in to continue."
                ),
            )

    # ── Step 1: Google Business data ──────────────────────────────────────────
    google_data = await search_business(req.business_name, req.location)

    # ── Resolve website URL — single source of truth ──────────────────────────
    # Priority: user-entered URL > Google listing URL
    raw_url    = req.website_url.strip() or google_data.get("website", "")
    website_url = normalise_url(raw_url)   # ← consistent across all services

    manual_socials = {
        "instagram_url": req.instagram_url.strip() if req.instagram_url else "",
        "facebook_url":  req.facebook_url.strip()  if req.facebook_url  else "",
        "linkedin_url":  req.linkedin_url.strip()  if req.linkedin_url  else "",
        "youtube_url":   req.youtube_url.strip()   if req.youtube_url   else "",
        "twitter_url":   req.twitter_url.strip()   if req.twitter_url   else "",
    }

    # ── Step 2: All parallel checks ───────────────────────────────────────────
    pagespeed_data, social_data, seo_data, competitor_data, auto_email = await asyncio.gather(
        analyze_website(website_url),
        check_social_presence(website_url, google_data, manual_socials),
        crawl_website(website_url),
        analyze_competitors(
            req.business_name, req.location,
            req.category or "General Business", google_data,
        ),
        discover_contact_email(website_url),
    )

    # ── Step 3: SEO AI recommendations ───────────────────────────────────────
    seo_data["recommendations"] = generate_seo_recommendations(
        req.business_name,
        req.category or "General Business",
        req.location,
        seo_data,
    )

    # ── Step 4: Keyword extraction ────────────────────────────────────────────
    comp_urls = [
        c.get("website_url", "")
        for c in competitor_data.get("competitors", [])
        if c.get("website_url")
    ][:3]

    keyword_data = await extract_keywords(
        business_name=req.business_name,
        category=req.category or "General Business",
        location=req.location,
        target_url=website_url,
        competitor_urls=comp_urls,
    )

    # ── Step 5: Score ─────────────────────────────────────────────────────────
    score_data = calculate_score(
        google_data, pagespeed_data, social_data,
        category=req.category or "General Business",
        seo_data=seo_data,
    )

    # ── Step 6: AI insights ───────────────────────────────────────────────────
    ai_insights = generate_insights(
        req.business_name, req.location, score_data, google_data
    )

    # ── Step 7: Assemble ──────────────────────────────────────────────────────
    business_info = {
        "name":          google_data.get("name", req.business_name),
        "location":      req.location,
        "category":      req.category,
        "address":       google_data.get("address", ""),
        "phone":         google_data.get("phone", ""),
        "email":         auto_email,
        "website":       website_url,
        "rating":        google_data.get("rating", 0),
        "total_reviews": google_data.get("total_reviews", 0),
        "maps_url":      google_data.get("maps_url", ""),
        "is_mocked":     google_data.get("mocked", False),
    }

    full_result = {
        "business":    business_info,
        "score":       score_data,
        "pagespeed":   pagespeed_data,
        "social":      social_data,
        "seo":         seo_data,
        "competitors": competitor_data,
        "keywords":    keyword_data,
        "insights":    ai_insights,
    }

    # ── Step 8: Save lead silently ────────────────────────────────────────────
    lead_id = None
    search_id = None
    try:
        lead = await crud.create_lead(db, {
            "business_name": req.business_name,
            "location":      req.location,
            "category":      req.category,
            "website_url":   website_url,
            "instagram_url": req.instagram_url,
            "facebook_url":  req.facebook_url,
            "linkedin_url":  req.linkedin_url,
            "contact_phone": google_data.get("phone", "") or None,
            "contact_email": auto_email or None,
            "contact_captured_at": None,
            "total_score":   score_data.get("total_score"),
            "grade":         score_data.get("grade"),
            "score_label":   score_data.get("label"),
            "is_mocked":     google_data.get("mocked", False),
            "audit_json":    full_result,
            "ip_address":    requester_ip,
            "user_agent":    request.headers.get("user-agent"),
            "utm_source":    request.query_params.get("utm_source"),
            "utm_medium":    request.query_params.get("utm_medium"),
            "utm_campaign":  request.query_params.get("utm_campaign"),
        })
        lead_id = lead.id

        search = await crud.create_search_record(db, {
            "user_id":       user.id if user else None,
            "legacy_lead_id": lead.id,
            "business_name": req.business_name,
            "location":      req.location,
            "category":      req.category,
            "website_url":   website_url,
            "instagram_url": req.instagram_url,
            "facebook_url":  req.facebook_url,
            "linkedin_url":  req.linkedin_url,
            "youtube_url":   req.youtube_url,
            "twitter_url":   req.twitter_url,
            "auto_phone":    google_data.get("phone", "") or None,
            "auto_email":    auto_email or None,
            "total_score":   score_data.get("total_score"),
            "grade":         score_data.get("grade"),
            "score_label":   score_data.get("label"),
            "is_mocked":     google_data.get("mocked", False),
            "source_type":   "user" if user else "anonymous",
            "status":        "new",
            "audit_json":    full_result,
            "ip_address":    requester_ip,
            "user_agent":    request.headers.get("user-agent"),
            "utm_source":    request.query_params.get("utm_source"),
            "utm_medium":    request.query_params.get("utm_medium"),
            "utm_campaign":  request.query_params.get("utm_campaign"),
        })
        search_id = search.id

        if user:
            await crud.create_user_activity(
                db,
                user.id,
                "search_created",
                {
                    "search_id": search.id,
                    "business_name": req.business_name,
                    "location": req.location,
                    "score": score_data.get("total_score"),
                },
            )
    except Exception as e:
        print(f"[Lead Save] Failed: {e}")

    return JSONResponse(content={**full_result, "lead_id": lead_id, "search_id": search_id})


@router.post("/audit/pdf")
async def generate_report_pdf(
    req: AuditRequest,
    db: AsyncSession = Depends(get_db),
):
    if not req.business_name.strip():
        raise HTTPException(400, "Business name is required")

    google_data  = await search_business(req.business_name, req.location)
    raw_url      = req.website_url.strip() or google_data.get("website", "")
    website_url  = normalise_url(raw_url)

    manual_socials = {
        "instagram_url": req.instagram_url.strip() if req.instagram_url else "",
        "facebook_url":  req.facebook_url.strip()  if req.facebook_url  else "",
        "linkedin_url":  req.linkedin_url.strip()  if req.linkedin_url  else "",
        "youtube_url":   req.youtube_url.strip()   if req.youtube_url   else "",
        "twitter_url":   req.twitter_url.strip()   if req.twitter_url   else "",
    }

    pagespeed_data, social_data, seo_data, competitor_data = await asyncio.gather(
        analyze_website(website_url),
        check_social_presence(website_url, google_data, manual_socials),
        crawl_website(website_url),
        analyze_competitors(
            req.business_name, req.location,
            req.category or "General Business", google_data,
        ),
    )

    seo_data["recommendations"] = generate_seo_recommendations(
        req.business_name, req.category or "General Business", req.location, seo_data
    )

    keyword_data = await extract_keywords(
        business_name=req.business_name,
        category=req.category or "General Business",
        location=req.location,
        target_url=website_url,
        competitor_urls=[c.get("website_url", "") for c in
                         competitor_data.get("competitors", []) if c.get("website_url")][:3],
    )

    score_data  = calculate_score(
        google_data, pagespeed_data, social_data,
        category=req.category or "General Business",
        seo_data=seo_data,
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
        seo_data=seo_data,
        competitor_data=competitor_data,
        keyword_data=keyword_data,
    )

    filename = f"aidbro_health_{req.business_name.replace(' ', '_')}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/health")
def health_check():
    return {"status": "ok", "version": "2.0.0"}
