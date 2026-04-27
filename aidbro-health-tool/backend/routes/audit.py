import asyncio
import io
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database import crud
from database.connection import get_db
from services.ai_writer import generate_insights
from services.competitor_analyzer import analyze_competitors
from services.contact_finder import discover_contact_email
from services.google_places import search_business
from services.keyword_extractor import extract_keywords
from services.pagespeed import analyze_website, normalise_url
from services.pdf_generator import generate_pdf
from services.scorer import calculate_score
from services.seo_crawler import crawl_website
from services.seo_recommendations import generate_seo_recommendations
from services.social_check import check_social_presence
from utils.auth_utils import decode_token

router = APIRouter()

ANONYMOUS_AUDIT_LIMIT = 2
ANONYMOUS_AUDIT_WINDOW_DAYS = 7
AUDIT_RESULT_CACHE_HOURS = 24


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
    business_name: str
    location: str
    mobile_number: Optional[str] = ""
    category: Optional[str] = "General Business"
    website_url: Optional[str] = ""
    instagram_url: Optional[str] = ""
    facebook_url: Optional[str] = ""
    linkedin_url: Optional[str] = ""
    youtube_url: Optional[str] = ""
    twitter_url: Optional[str] = ""


def _manual_socials(req: AuditRequest) -> dict:
    return {
        "instagram_url": req.instagram_url.strip() if req.instagram_url else "",
        "facebook_url": req.facebook_url.strip() if req.facebook_url else "",
        "linkedin_url": req.linkedin_url.strip() if req.linkedin_url else "",
        "youtube_url": req.youtube_url.strip() if req.youtube_url else "",
        "twitter_url": req.twitter_url.strip() if req.twitter_url else "",
    }


def _save_payload(
    req: AuditRequest,
    request: Request,
    user,
    requester_ip: Optional[str],
    website_url: str,
    google_data: dict,
    auto_email: Optional[str],
    full_result: dict,
):
    score_data = full_result.get("score", {})
    return {
        "user_id": user.id if user else None,
        "business_name": req.business_name,
        "location": req.location,
        "category": req.category,
        "website_url": website_url,
        "instagram_url": req.instagram_url,
        "facebook_url": req.facebook_url,
        "linkedin_url": req.linkedin_url,
        "youtube_url": req.youtube_url,
        "twitter_url": req.twitter_url,
        "auto_phone": google_data.get("phone", "") or None,
        "auto_email": auto_email or None,
        "manual_contact_phone": req.mobile_number.strip() or None,
        "manual_contact_captured_at": datetime.now(timezone.utc) if req.mobile_number.strip() else None,
        "total_score": score_data.get("total_score"),
        "grade": score_data.get("grade"),
        "score_label": score_data.get("label"),
        "is_mocked": google_data.get("mocked", False),
        "audit_json": full_result,
        "ip_address": requester_ip,
        "user_agent": request.headers.get("user-agent"),
        "utm_source": request.query_params.get("utm_source"),
        "utm_medium": request.query_params.get("utm_medium"),
        "utm_campaign": request.query_params.get("utm_campaign"),
    }


def _build_cached_google_data(full_result: dict, fallback_name: str) -> dict:
    business = full_result.get("business", {})
    return {
        "found": business.get(
            "google_profile_found",
            business.get("rating", 0) > 0
            or bool(business.get("phone"))
            or bool(business.get("maps_url")),
        ),
        "name": business.get("name", fallback_name),
        "address": business.get("address", ""),
        "phone": business.get("phone", ""),
        "website": business.get("website", ""),
        "rating": business.get("rating", 0),
        "total_reviews": business.get("total_reviews", 0),
        "match_confidence": business.get("google_match_confidence", ""),
        "match_score": business.get("google_match_score", 0),
        "match_warning": business.get("google_match_warning", ""),
        "matched_profile_name": business.get(
            "matched_profile_name",
            business.get("name", fallback_name),
        ),
        "matched_profile_address": business.get(
            "matched_profile_address",
            business.get("address", ""),
        ),
        "maps_url": business.get("maps_url", ""),
        "mocked": business.get("is_mocked", False),
    }


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
    if not req.mobile_number.strip():
        raise HTTPException(400, "Mobile number is required")

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

    manual_social_inputs = _manual_socials(req)
    website_hint = normalise_url(req.website_url.strip()) if req.website_url else None

    full_result = None
    google_data = {}
    auto_email = None

    if not any(manual_social_inputs.values()):
        cache_since = datetime.now(timezone.utc) - timedelta(hours=AUDIT_RESULT_CACHE_HOURS)
        cached_search = await crud.get_recent_matching_search(
            db,
            business_name=req.business_name,
            location=req.location,
            category=req.category or "General Business",
            website_url=website_hint,
            since=cache_since,
        )
        if cached_search and cached_search.audit_json:
            full_result = cached_search.audit_json
            google_data = _build_cached_google_data(full_result, req.business_name)
            auto_email = full_result.get("business", {}).get("email", "")

    if full_result is None:
        google_data = await search_business(
            req.business_name,
            req.location,
            req.website_url.strip(),
        )
        raw_url = req.website_url.strip() or google_data.get("website", "")
        website_url = normalise_url(raw_url)

        pagespeed_data, social_data, seo_data, competitor_data, auto_email = await asyncio.gather(
            analyze_website(website_url),
            check_social_presence(website_url, google_data, manual_social_inputs),
            crawl_website(website_url),
            analyze_competitors(
                req.business_name,
                req.location,
                req.category or "General Business",
                google_data,
            ),
            discover_contact_email(website_url),
        )

        seo_data["recommendations"] = generate_seo_recommendations(
            req.business_name,
            req.category or "General Business",
            req.location,
            seo_data,
        )

        comp_urls = [
            item.get("website_url", "")
            for item in competitor_data.get("competitors", [])
            if item.get("website_url")
        ][:3]

        keyword_data = await extract_keywords(
            business_name=req.business_name,
            category=req.category or "General Business",
            location=req.location,
            target_url=website_url,
            competitor_urls=comp_urls,
        )

        score_data = calculate_score(
            google_data,
            pagespeed_data,
            social_data,
            category=req.category or "General Business",
            seo_data=seo_data,
        )
        ai_insights = generate_insights(req.business_name, req.location, score_data, google_data)

        business_info = {
            "name": google_data.get("name", req.business_name),
            "location": req.location,
            "category": req.category,
            "address": google_data.get("address", ""),
            "phone": google_data.get("phone", ""),
            "email": auto_email,
            "website": website_url,
            "rating": google_data.get("rating", 0),
            "total_reviews": google_data.get("total_reviews", 0),
            "maps_url": google_data.get("maps_url", ""),
            "google_profile_found": google_data.get("found", False),
            "google_match_confidence": google_data.get("match_confidence", ""),
            "google_match_score": google_data.get("match_score", 0),
            "google_match_warning": google_data.get("match_warning", ""),
            "matched_profile_name": google_data.get(
                "matched_profile_name",
                google_data.get("name", req.business_name),
            ),
            "matched_profile_address": google_data.get(
                "matched_profile_address",
                google_data.get("address", ""),
            ),
            "is_mocked": google_data.get("mocked", False),
        }

        full_result = {
            "business": business_info,
            "score": score_data,
            "pagespeed": pagespeed_data,
            "social": social_data,
            "seo": seo_data,
            "competitors": competitor_data,
            "keywords": keyword_data,
            "insights": ai_insights,
        }
    else:
        raw_url = req.website_url.strip() or google_data.get("website", "")
        website_url = normalise_url(raw_url)

    lead_id = None
    search_id = None
    score_data = full_result.get("score", {})

    try:
        save_data = _save_payload(
            req,
            request,
            user,
            requester_ip,
            website_url,
            google_data,
            auto_email,
            full_result,
        )

        lead = await crud.create_lead(
            db,
            {
                "business_name": save_data["business_name"],
                "location": save_data["location"],
                "category": save_data["category"],
                "website_url": save_data["website_url"],
                "instagram_url": save_data["instagram_url"],
                "facebook_url": save_data["facebook_url"],
                "linkedin_url": save_data["linkedin_url"],
                "contact_phone": save_data["manual_contact_phone"] or save_data["auto_phone"],
                "contact_email": save_data["auto_email"],
                "contact_captured_at": save_data["manual_contact_captured_at"],
                "total_score": save_data["total_score"],
                "grade": save_data["grade"],
                "score_label": save_data["score_label"],
                "is_mocked": save_data["is_mocked"],
                "audit_json": save_data["audit_json"],
                "ip_address": save_data["ip_address"],
                "user_agent": save_data["user_agent"],
                "utm_source": save_data["utm_source"],
                "utm_medium": save_data["utm_medium"],
                "utm_campaign": save_data["utm_campaign"],
            },
        )
        lead_id = lead.id

        search = await crud.create_search_record(
            db,
            {
                **save_data,
                "legacy_lead_id": lead.id,
                "source_type": "user" if user else "anonymous",
                "status": "new",
            },
        )
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
    except Exception as exc:
        print(f"[Lead Save] Failed: {exc}")

    return JSONResponse(
        content={
            **full_result,
            "lead_id": lead_id,
            "search_id": search_id,
        }
    )


@router.post("/audit/pdf")
async def generate_report_pdf(
    req: AuditRequest,
    db: AsyncSession = Depends(get_db),
):
    if not req.business_name.strip():
        raise HTTPException(400, "Business name is required")

    google_data = await search_business(
        req.business_name,
        req.location,
        req.website_url.strip(),
    )
    raw_url = req.website_url.strip() or google_data.get("website", "")
    website_url = normalise_url(raw_url)
    manual_social_inputs = _manual_socials(req)

    pagespeed_data, social_data, seo_data, competitor_data = await asyncio.gather(
        analyze_website(website_url),
        check_social_presence(website_url, google_data, manual_social_inputs),
        crawl_website(website_url),
        analyze_competitors(
            req.business_name,
            req.location,
            req.category or "General Business",
            google_data,
        ),
    )

    seo_data["recommendations"] = generate_seo_recommendations(
        req.business_name,
        req.category or "General Business",
        req.location,
        seo_data,
    )

    keyword_data = await extract_keywords(
        business_name=req.business_name,
        category=req.category or "General Business",
        location=req.location,
        target_url=website_url,
        competitor_urls=[
            item.get("website_url", "")
            for item in competitor_data.get("competitors", [])
            if item.get("website_url")
        ][:3],
    )

    score_data = calculate_score(
        google_data,
        pagespeed_data,
        social_data,
        category=req.category or "General Business",
        seo_data=seo_data,
    )
    ai_insights = generate_insights(req.business_name, req.location, score_data, google_data)

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
