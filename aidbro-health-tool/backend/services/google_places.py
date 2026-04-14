import os
import httpx
from typing import Optional

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# ─── Mock data for prototype testing without API key ───────────────────────────
MOCK_BUSINESS = {
    "found": True,
    "mocked": True,
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
    ]
}


async def search_business(business_name: str, location: str) -> dict:
    """
    Search for a business using Google Places API.
    Falls back to realistic mock data when API key is missing.
    """

    if not GOOGLE_API_KEY or GOOGLE_API_KEY == "your_google_key_here":
        print("[Places] No API key — returning mock data for prototype")
        mock = dict(MOCK_BUSINESS)
        mock["name"] = business_name + " (Demo Mode)"
        mock["address"] = f"{location}, Kerala"
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
            )
        }
        payload = {
            "textQuery": query,
            "languageCode": "en",
            "maxResultCount": 1
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            data = response.json()

        if "places" not in data or not data["places"]:
            return {"found": False, "mocked": False, "name": business_name}

        place = data["places"][0]
        place_id = place.get("id", "")

        business = {
            "found": True,
            "mocked": False,
            "name": place.get("displayName", {}).get("text", business_name),
            "address": place.get("formattedAddress", ""),
            "phone": place.get("internationalPhoneNumber", ""),
            "website": place.get("websiteUri", ""),
            "rating": place.get("rating", 0),
            "total_reviews": place.get("userRatingCount", 0),
            "photos_count": len(place.get("photos", [])),
            "has_hours": bool(place.get("regularOpeningHours")),
            "has_description": bool(place.get("editorialSummary", {}).get("text")),
            "business_status": place.get("businessStatus", "UNKNOWN"),
            "maps_url": place.get("googleMapsUri", ""),
            "place_id": place_id,
        }

        # ── Fetch nearby competitors ──────────────────────────────────────────
        business["nearby_competitors"] = await _get_nearby_competitors(
            business_name, location
        )

        return business

    except Exception as e:
        print(f"[Places] Error: {e} — falling back to mock")
        mock = dict(MOCK_BUSINESS)
        mock["name"] = business_name + " (Demo Mode)"
        mock["address"] = f"{location}, Kerala"
        return mock


async def _get_nearby_competitors(business_name: str, location: str) -> list:
    """Fetch up to 3 nearby businesses in the same category."""
    if not GOOGLE_API_KEY:
        return MOCK_BUSINESS["nearby_competitors"]

    try:
        url = "https://places.googleapis.com/v1/places:searchText"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": GOOGLE_API_KEY,
            "X-Goog-FieldMask": "places.displayName,places.rating,places.userRatingCount"
        }
        payload = {
            "textQuery": f"businesses near {location} Kerala",
            "maxResultCount": 5
        }

        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            data = response.json()

        competitors = []
        for p in data.get("places", [])[:3]:
            name = p.get("displayName", {}).get("text", "Unknown")
            if business_name.lower() not in name.lower():
                competitors.append({
                    "name": name,
                    "rating": p.get("rating", 0),
                    "reviews": p.get("userRatingCount", 0)
                })

        return competitors if competitors else MOCK_BUSINESS["nearby_competitors"]

    except Exception:
        return MOCK_BUSINESS["nearby_competitors"]