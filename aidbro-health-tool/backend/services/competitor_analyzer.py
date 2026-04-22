"""
Competitor Analyzer
====================
Fetches up to 5 local competitors from Google Places API
and builds a full side-by-side comparison with AI gap analysis.

Data per competitor (all from Places API):
  name, rating, review_count, has_website, website_url,
  photos_count, has_hours, has_description, categories,
  distance, maps_url

Comparison dimensions:
  Star Rating, Review Count, Website Presence,
  Photo Count, Profile Completeness, Category Coverage
"""

import os
import json
import httpx
from groq import Groq

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GROQ_API_KEY   = os.getenv("GROQ_API_KEY", "")

# ── Mock competitors for demo mode ────────────────────────────────────────────
MOCK_COMPETITORS = [
    {
        "name": "Alpha Digital Solutions",
        "rating": 4.5, "review_count": 87,
        "has_website": True,  "website_url": "https://example-alpha.com",
        "photos_count": 24,   "has_hours": True,
        "has_description": True, "categories": ["IT Services"],
        "distance": "0.4 km",    "maps_url": "#",
        "profile_completeness": 92,
    },
    {
        "name": "Beta Tech Hub",
        "rating": 4.2, "review_count": 54,
        "has_website": True,  "website_url": "https://example-beta.com",
        "photos_count": 12,   "has_hours": True,
        "has_description": True, "categories": ["Software Company"],
        "distance": "0.9 km",    "maps_url": "#",
        "profile_completeness": 78,
    },
    {
        "name": "Gamma Innovations",
        "rating": 3.9, "review_count": 31,
        "has_website": False, "website_url": "",
        "photos_count": 5,    "has_hours": False,
        "has_description": False, "categories": ["Computer Store"],
        "distance": "1.2 km",    "maps_url": "#",
        "profile_completeness": 45,
    },
    {
        "name": "Delta Web Services",
        "rating": 4.0, "review_count": 19,
        "has_website": True,  "website_url": "https://example-delta.com",
        "photos_count": 8,    "has_hours": True,
        "has_description": False, "categories": ["Web Designer"],
        "distance": "1.5 km",    "maps_url": "#",
        "profile_completeness": 60,
    },
    {
        "name": "Epsilon Media Group",
        "rating": 4.7, "review_count": 143,
        "has_website": True,  "website_url": "https://example-epsilon.com",
        "photos_count": 38,   "has_hours": True,
        "has_description": True, "categories": ["Marketing Agency"],
        "distance": "2.1 km",    "maps_url": "#",
        "profile_completeness": 97,
    },
]


async def analyze_competitors(
    business_name: str,
    location: str,
    category: str,
    target_business: dict,
) -> dict:
    """
    Fetch local competitors and build a full comparison.

    Args:
        business_name:   The audited business name
        location:        City / area
        category:        Business category (for relevance)
        target_business: The audited business's Google Places data

    Returns:
        {
          "competitors":   list of competitor dicts,
          "comparison":    comparison matrix dict,
          "gaps":          list of gap objects,
          "ai_summary":    str,
          "is_mocked":     bool,
        }
    """
    competitors = await _fetch_competitors(business_name, location, category)
    is_mocked   = not bool(GOOGLE_API_KEY and GOOGLE_API_KEY != "your_google_key_here")

    if not competitors:
        competitors = MOCK_COMPETITORS
        is_mocked   = True

    # ── Build target business profile ─────────────────────────────────────────
    target = {
        "name":                 business_name,
        "rating":               target_business.get("rating", 0),
        "review_count":         target_business.get("total_reviews", 0),
        "has_website":          bool(target_business.get("website")),
        "website_url":          target_business.get("website", ""),
        "photos_count":         target_business.get("photos_count", 0),
        "has_hours":            target_business.get("has_hours", False),
        "has_description":      target_business.get("has_description", False),
        "profile_completeness": _calc_completeness(target_business),
    }

    # ── Build comparison matrix ────────────────────────────────────────────────
    comparison = _build_comparison(target, competitors)

    # ── Identify gaps ─────────────────────────────────────────────────────────
    gaps = _identify_gaps(target, competitors)

    # ── AI gap summary ────────────────────────────────────────────────────────
    ai_summary = _generate_ai_summary(
        business_name, category, location, target, competitors, gaps
    )

    return {
        "target":      target,
        "competitors": competitors,
        "comparison":  comparison,
        "gaps":        gaps,
        "ai_summary":  ai_summary,
        "is_mocked":   is_mocked,
    }


async def _fetch_competitors(
    business_name: str,
    location: str,
    category: str,
) -> list:
    """Fetch up to 5 nearby competitors from Google Places API."""
    if not GOOGLE_API_KEY or GOOGLE_API_KEY == "your_google_key_here":
        return []

    try:
        query = f"{category} in {location}"
        url   = "https://places.googleapis.com/v1/places:searchText"
        headers = {
            "Content-Type":    "application/json",
            "X-Goog-Api-Key":  GOOGLE_API_KEY,
            "X-Goog-FieldMask": (
                "places.id,places.displayName,places.formattedAddress,"
                "places.rating,places.userRatingCount,places.photos,"
                "places.regularOpeningHours,places.editorialSummary,"
                "places.websiteUri,places.types,places.googleMapsUri"
            ),
        }
        payload = {
            "textQuery":     query,
            "maxResultCount": 8,
            "languageCode":  "en",
        }

        async with httpx.AsyncClient(timeout=12.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            data     = response.json()

        competitors = []
        for place in data.get("places", []):
            name = place.get("displayName", {}).get("text", "")
            # Skip the business being audited
            if business_name.lower() in name.lower():
                continue

            comp = {
                "name":         name,
                "rating":       place.get("rating", 0),
                "review_count": place.get("userRatingCount", 0),
                "has_website":  bool(place.get("websiteUri")),
                "website_url":  place.get("websiteUri", ""),
                "photos_count": len(place.get("photos", [])),
                "has_hours":    bool(place.get("regularOpeningHours")),
                "has_description": bool(
                    place.get("editorialSummary", {}).get("text")
                ),
                "categories":   place.get("types", [])[:3],
                "maps_url":     place.get("googleMapsUri", ""),
                "distance":     "",
            }
            comp["profile_completeness"] = _calc_completeness_from_place(comp)
            competitors.append(comp)

            if len(competitors) >= 5:
                break

        return competitors

    except Exception as e:
        print(f"[Competitor] Fetch error: {e}")
        return []


def _calc_completeness(google_data: dict) -> int:
    """Calculate profile completeness % for the audited business."""
    score = 0
    if google_data.get("rating", 0) > 0:            score += 15
    if google_data.get("total_reviews", 0) >= 5:     score += 20
    if google_data.get("website"):                   score += 20
    if google_data.get("photos_count", 0) >= 5:      score += 15
    if google_data.get("has_hours"):                 score += 15
    if google_data.get("has_description"):           score += 10
    if google_data.get("phone"):                     score += 5
    return score


def _calc_completeness_from_place(comp: dict) -> int:
    """Calculate profile completeness % for a competitor."""
    score = 0
    if comp.get("rating", 0) > 0:       score += 15
    if comp.get("review_count", 0) >= 5: score += 20
    if comp.get("has_website"):          score += 20
    if comp.get("photos_count", 0) >= 5: score += 15
    if comp.get("has_hours"):            score += 15
    if comp.get("has_description"):      score += 10
    score += 5  # assume phone is listed
    return score


def _build_comparison(target: dict, competitors: list) -> dict:
    """
    Build a comparison matrix across all dimensions.
    Each dimension: who wins, by how much, is it a gap.
    """
    all_businesses = [target] + competitors

    def winner_index(key, higher_is_better=True):
        """Return index of winner (0 = target, 1-5 = competitors)."""
        vals = [b.get(key, 0) for b in all_businesses]
        return vals.index(max(vals) if higher_is_better else min(vals))

    avg_comp_reviews = (
        sum(c.get("review_count", 0) for c in competitors) / len(competitors)
        if competitors else 0
    )
    avg_comp_rating = (
        sum(c.get("rating", 0) for c in competitors) / len(competitors)
        if competitors else 0
    )
    avg_comp_photos = (
        sum(c.get("photos_count", 0) for c in competitors) / len(competitors)
        if competitors else 0
    )

    return {
        "dimensions": [
            {
                "key":   "rating",
                "label": "Star Rating",
                "icon":  "⭐",
                "target_value": target["rating"],
                "competitor_avg": round(avg_comp_rating, 1),
                "target_wins": target["rating"] >= avg_comp_rating,
                "unit": "★",
            },
            {
                "key":   "review_count",
                "label": "Review Count",
                "icon":  "💬",
                "target_value": target["review_count"],
                "competitor_avg": round(avg_comp_reviews),
                "target_wins": target["review_count"] >= avg_comp_reviews,
                "unit": "",
            },
            {
                "key":   "has_website",
                "label": "Website",
                "icon":  "🌐",
                "target_value": "Yes" if target["has_website"] else "No",
                "competitor_avg": f"{sum(1 for c in competitors if c.get('has_website'))}/{len(competitors)} have",
                "target_wins": target["has_website"],
                "unit": "",
            },
            {
                "key":   "photos_count",
                "label": "Photos",
                "icon":  "📸",
                "target_value": target["photos_count"],
                "competitor_avg": round(avg_comp_photos),
                "target_wins": target["photos_count"] >= avg_comp_photos,
                "unit": "",
            },
            {
                "key":   "profile_completeness",
                "label": "Profile Complete",
                "icon":  "✅",
                "target_value": target["profile_completeness"],
                "competitor_avg": round(
                    sum(c.get("profile_completeness", 0) for c in competitors)
                    / len(competitors)
                ) if competitors else 0,
                "target_wins": target["profile_completeness"] >= (
                    sum(c.get("profile_completeness", 0) for c in competitors)
                    / len(competitors)
                    if competitors else 0
                ),
                "unit": "%",
            },
        ],
        "competitors_with_website": sum(1 for c in competitors if c.get("has_website")),
        "strongest_competitor": max(
            competitors, key=lambda c: c.get("review_count", 0)
        )["name"] if competitors else "N/A",
        "avg_competitor_reviews": round(avg_comp_reviews),
        "avg_competitor_rating":  round(avg_comp_rating, 1),
    }


def _identify_gaps(target: dict, competitors: list) -> list:
    """Identify the most important gaps vs competitors."""
    gaps = []
    if not competitors:
        return gaps

    avg_reviews = sum(c.get("review_count", 0) for c in competitors) / len(competitors)
    avg_rating  = sum(c.get("rating", 0) for c in competitors) / len(competitors)
    avg_photos  = sum(c.get("photos_count", 0) for c in competitors) / len(competitors)

    # Review gap
    if target["review_count"] < avg_reviews:
        diff = round(avg_reviews - target["review_count"])
        gaps.append({
            "dimension": "Reviews",
            "severity":  "critical" if diff > 20 else "warning",
            "message":   f"You need {diff} more reviews to match the local average.",
            "action":    "Start a WhatsApp review request campaign this week.",
            "service":   "Digital Marketing",
        })

    # Rating gap
    if target["rating"] > 0 and target["rating"] < avg_rating - 0.2:
        gaps.append({
            "dimension": "Star Rating",
            "severity":  "critical",
            "message":   f"Your {target['rating']}★ is below the local average of {round(avg_rating,1)}★.",
            "action":    "Respond to all negative reviews and resolve complaints directly.",
            "service":   "Digital Marketing",
        })

    # Website gap
    website_count = sum(1 for c in competitors if c.get("has_website"))
    if not target["has_website"] and website_count >= 2:
        gaps.append({
            "dimension": "Website",
            "severity":  "critical",
            "message":   f"{website_count} of your {len(competitors)} competitors have websites. You don't.",
            "action":    "Get a professional website built — this is the single biggest digital gap.",
            "service":   "Web Development",
        })

    # Photos gap
    if target["photos_count"] < avg_photos - 3:
        gaps.append({
            "dimension": "Google Photos",
            "severity":  "warning",
            "message":   f"Competitors average {round(avg_photos)} photos vs your {target['photos_count']}.",
            "action":    "Upload at least 10 high-quality photos to your Google listing today.",
            "service":   "Digital Marketing",
        })

    # Profile completeness gap
    avg_completeness = sum(c.get("profile_completeness", 0) for c in competitors) / len(competitors)
    if target["profile_completeness"] < avg_completeness - 10:
        gaps.append({
            "dimension": "Profile Completeness",
            "severity":  "warning",
            "message":   f"Your profile is {target['profile_completeness']}% complete vs competitor average of {round(avg_completeness)}%.",
            "action":    "Complete all fields in your Google Business Profile — categories, services, description.",
            "service":   "Digital Marketing",
        })

    return gaps


def _generate_ai_summary(
    business_name: str,
    category: str,
    location: str,
    target: dict,
    competitors: list,
    gaps: list,
) -> str:
    """Generate a 2-3 sentence AI summary of the competitive position."""
    if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_key_here":
        return _fallback_summary(business_name, target, competitors, gaps)

    try:
        strongest = max(competitors, key=lambda c: c.get("review_count", 0))
        avg_rev   = round(sum(c.get("review_count", 0) for c in competitors) / len(competitors))

        prompt = f"""Write a 2-sentence competitive intelligence summary for {business_name},
a {category} in {location}.

Their stats: {target['review_count']} reviews, {target['rating']}★, 
profile {target['profile_completeness']}% complete.

Strongest competitor: {strongest['name']} with {strongest['review_count']} reviews 
and {strongest['rating']}★.

Local average: {avg_rev} reviews.
Key gaps: {', '.join(g['dimension'] for g in gaps[:3]) if gaps else 'None identified'}.

Be specific, honest, and urgent. No fluff. Plain language for a local business owner."""

        client   = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=120,
            temperature=0.6,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"[Competitor AI] Error: {e}")
        return _fallback_summary(business_name, target, competitors, gaps)


def _fallback_summary(
    business_name: str,
    target: dict,
    competitors: list,
    gaps: list,
) -> str:
    if not competitors:
        return f"No competitor data available for {business_name}."

    strongest = max(competitors, key=lambda c: c.get("review_count", 0))
    avg_rev   = round(sum(c.get("review_count", 0) for c in competitors) / len(competitors))

    if target["review_count"] < avg_rev:
        return (
            f"Your strongest local competitor, {strongest['name']}, has "
            f"{strongest['review_count']} reviews compared to your {target['review_count']}. "
            f"The local average is {avg_rev} reviews — closing this gap should be your immediate priority."
        )
    else:
        return (
            f"{business_name} is ahead of the local average on reviews ({target['review_count']} vs {avg_rev}). "
            f"Focus on maintaining this lead and closing any remaining profile gaps to stay dominant in local search."
        )
