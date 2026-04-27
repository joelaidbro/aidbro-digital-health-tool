import os
import re
from difflib import SequenceMatcher
from typing import Optional
from urllib.parse import urlparse

import httpx

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

MOCK_BUSINESS = {
    "found": True,
    "mocked": True,
    "match_confidence": "mock",
    "match_score": 1.0,
    "match_warning": "",
    "matched_profile_name": "Sample Business (Demo Mode)",
    "matched_profile_address": "MG Road, Kannur, Kerala 670001",
    "name": "Sample Business (Demo Mode)",
    "address": "MG Road, Kannur, Kerala 670001",
    "phone": "+91 98765 43210",
    "website": "https://example.com",
    "rating": 3.8,
    "total_reviews": 22,
    "photos_count": 4,
    "has_hours": True,
    "has_description": False,
    "business_status": "OPERATIONAL",
    "maps_url": "https://maps.google.com",
    "place_id": "mock_place_id_001",
    "nearby_competitors": [
        {"name": "Competitor A", "rating": 4.5, "reviews": 87},
        {"name": "Competitor B", "rating": 4.2, "reviews": 54},
        {"name": "Competitor C", "rating": 3.9, "reviews": 31},
    ],
}

STOPWORDS = {
    "and",
    "at",
    "by",
    "for",
    "group",
    "in",
    "india",
    "international",
    "kerala",
    "llp",
    "ltd",
    "near",
    "of",
    "pvt",
    "services",
    "solutions",
    "the",
}


def _normalise_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def _tokenise(value: str) -> set[str]:
    tokens = {token for token in _normalise_text(value).split() if len(token) > 1}
    return {token for token in tokens if token not in STOPWORDS}


def _domain_from_url(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url if "://" in url else f"https://{url}")
    return parsed.netloc.lower().removeprefix("www.")


def _build_low_confidence_result(
    business_name: str,
    location: str,
    candidate: Optional[dict] = None,
    score: float = 0.0,
) -> dict:
    candidate_name = candidate.get("displayName", {}).get("text", "") if candidate else ""
    candidate_address = candidate.get("formattedAddress", "") if candidate else ""
    warning = (
        "We could not confidently match this business to an exact Google profile, so "
        "Google profile scoring was skipped to avoid showing the wrong company."
    )
    if candidate_name:
        warning += f" Closest profile found: {candidate_name}"
        if candidate_address:
            warning += f" ({candidate_address})"
        warning += "."

    return {
        "found": False,
        "mocked": False,
        "match_confidence": "low",
        "match_score": round(score, 2),
        "match_warning": warning,
        "matched_profile_name": candidate_name,
        "matched_profile_address": candidate_address,
        "name": business_name,
        "address": "",
        "phone": "",
        "website": "",
        "rating": 0,
        "total_reviews": 0,
        "photos_count": 0,
        "has_hours": False,
        "has_description": False,
        "business_status": "UNCONFIRMED",
        "maps_url": "",
        "place_id": "",
        "nearby_competitors": [],
        "location": location,
    }


def _score_candidate(
    business_name: str,
    location: str,
    website_hint: str,
    candidate: dict,
) -> tuple[float, str]:
    requested_name = _normalise_text(business_name)
    candidate_name = _normalise_text(candidate.get("displayName", {}).get("text", ""))
    requested_tokens = _tokenise(business_name)
    candidate_tokens = _tokenise(candidate.get("displayName", {}).get("text", ""))
    location_tokens = _tokenise(location)
    address_tokens = _tokenise(candidate.get("formattedAddress", ""))

    ratio = SequenceMatcher(None, requested_name, candidate_name).ratio()
    overlap = (
        len(requested_tokens & candidate_tokens) / len(requested_tokens)
        if requested_tokens
        else 0.0
    )
    location_overlap = (
        len(location_tokens & address_tokens) / len(location_tokens)
        if location_tokens
        else 0.0
    )

    score = (ratio * 0.45) + (overlap * 0.35) + (location_overlap * 0.20)

    if requested_name == candidate_name:
        score += 0.25
    elif requested_name and candidate_name and (
        requested_name in candidate_name or candidate_name in requested_name
    ):
        score += 0.12

    requested_domain = _domain_from_url(website_hint)
    candidate_domain = _domain_from_url(candidate.get("websiteUri", ""))
    if requested_domain and candidate_domain:
        if requested_domain == candidate_domain:
            score += 0.30
        elif requested_domain.split(".")[0] == candidate_domain.split(".")[0]:
            score += 0.15

    score = min(score, 1.0)

    if score >= 0.78:
        return score, "high"
    if score >= 0.56:
        return score, "medium"
    return score, "low"


def _select_best_candidate(
    business_name: str,
    location: str,
    website_hint: str,
    places: list[dict],
) -> tuple[Optional[dict], float, str]:
    best_place = None
    best_score = -1.0
    best_confidence = "low"

    for place in places:
        score, confidence = _score_candidate(business_name, location, website_hint, place)
        if score > best_score:
            best_place = place
            best_score = score
            best_confidence = confidence

    return best_place, best_score, best_confidence


async def search_business(business_name: str, location: str, website_hint: str = "") -> dict:
    if not GOOGLE_API_KEY or GOOGLE_API_KEY == "your_google_key_here":
        print("[Places] No API key - returning mock data for prototype")
        mock = dict(MOCK_BUSINESS)
        mock["name"] = business_name + " (Demo Mode)"
        mock["address"] = f"{location}, Kerala"
        mock["matched_profile_name"] = mock["name"]
        mock["matched_profile_address"] = mock["address"]
        return mock

    try:
        query = f"{business_name} {location}"
        url = "https://places.googleapis.com/v1/places:searchText"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": GOOGLE_API_KEY,
            "X-Goog-FieldMask": (
                "places.id,places.displayName,places.formattedAddress,"
                "places.internationalPhoneNumber,places.websiteUri,"
                "places.rating,places.userRatingCount,places.photos,"
                "places.regularOpeningHours,places.editorialSummary,"
                "places.businessStatus,places.googleMapsUri"
            ),
        }
        payload = {
            "textQuery": query,
            "languageCode": "en",
            "maxResultCount": 5,
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            data = response.json()

        places = data.get("places", [])
        if not places:
            return {
                "found": False,
                "mocked": False,
                "name": business_name,
                "match_confidence": "low",
                "match_score": 0.0,
                "match_warning": (
                    "No confident Google Business Profile match was found for this business name and location. "
                    "Google profile scoring was skipped to avoid showing the wrong company."
                ),
                "matched_profile_name": "",
                "matched_profile_address": "",
            }

        place, match_score, match_confidence = _select_best_candidate(
            business_name,
            location,
            website_hint,
            places,
        )
        if not place:
            return {
                "found": False,
                "mocked": False,
                "name": business_name,
                "match_confidence": "low",
                "match_score": 0.0,
                "match_warning": (
                    "No confident Google Business Profile match was found for this business name and location. "
                    "Google profile scoring was skipped to avoid showing the wrong company."
                ),
                "matched_profile_name": "",
                "matched_profile_address": "",
            }
        if match_confidence == "low":
            return _build_low_confidence_result(
                business_name,
                location,
                candidate=place,
                score=match_score,
            )

        matched_name = place.get("displayName", {}).get("text", business_name)
        matched_address = place.get("formattedAddress", "")
        match_warning = ""
        if match_confidence == "medium":
            match_warning = (
                f"Google found the closest matching profile \"{matched_name}\". "
                "Please verify that this is your exact business before relying on the Google profile metrics."
            )

        business = {
            "found": True,
            "mocked": False,
            "match_confidence": match_confidence,
            "match_score": round(match_score, 2),
            "match_warning": match_warning,
            "matched_profile_name": matched_name,
            "matched_profile_address": matched_address,
            "name": matched_name,
            "address": matched_address,
            "phone": place.get("internationalPhoneNumber", ""),
            "website": place.get("websiteUri", ""),
            "rating": place.get("rating", 0),
            "total_reviews": place.get("userRatingCount", 0),
            "photos_count": len(place.get("photos", [])),
            "has_hours": bool(place.get("regularOpeningHours")),
            "has_description": bool(place.get("editorialSummary", {}).get("text")),
            "business_status": place.get("businessStatus", "UNKNOWN"),
            "maps_url": place.get("googleMapsUri", ""),
            "place_id": place.get("id", ""),
        }

        business["nearby_competitors"] = await _get_nearby_competitors(
            business_name,
            location,
        )
        return business

    except Exception as e:
        print(f"[Places] Error: {e} - falling back to mock")
        mock = dict(MOCK_BUSINESS)
        mock["name"] = business_name + " (Demo Mode)"
        mock["address"] = f"{location}, Kerala"
        mock["matched_profile_name"] = mock["name"]
        mock["matched_profile_address"] = mock["address"]
        return mock


async def _get_nearby_competitors(business_name: str, location: str) -> list:
    if not GOOGLE_API_KEY:
        return MOCK_BUSINESS["nearby_competitors"]

    try:
        url = "https://places.googleapis.com/v1/places:searchText"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": GOOGLE_API_KEY,
            "X-Goog-FieldMask": "places.displayName,places.rating,places.userRatingCount",
        }
        payload = {
            "textQuery": f"businesses near {location} Kerala",
            "maxResultCount": 5,
        }

        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            data = response.json()

        competitors = []
        for place in data.get("places", [])[:3]:
            name = place.get("displayName", {}).get("text", "Unknown")
            if business_name.lower() not in name.lower():
                competitors.append(
                    {
                        "name": name,
                        "rating": place.get("rating", 0),
                        "reviews": place.get("userRatingCount", 0),
                    }
                )

        return competitors if competitors else MOCK_BUSINESS["nearby_competitors"]

    except Exception:
        return MOCK_BUSINESS["nearby_competitors"]
