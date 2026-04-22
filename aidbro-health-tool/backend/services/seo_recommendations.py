"""
SEO AI Recommendations
=======================
Takes SEO crawler results and generates 5 specific,
prioritised recommendations using Groq (Llama 3.3).
"""

import os
import json
from groq import Groq

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")


def generate_seo_recommendations(
    business_name: str,
    category: str,
    location: str,
    seo_data: dict,
) -> list:
    """
    Generate 5 AI-powered SEO recommendations from crawler results.

    Returns a list of 5 dicts:
    [
      {
        "priority": 1,
        "title":    str,
        "problem":  str,
        "fix":      str,
        "impact":   "High" | "Medium" | "Low",
        "service":  str,   # Which Aidbro service addresses this
      },
      ...
    ]
    """
    if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_key_here":
        return _fallback_recommendations(seo_data)

    try:
        summary   = seo_data.get("summary", {})
        issues    = seo_data.get("issues", [])[:8]
        site      = seo_data.get("site_level", {})

        # Build a compact context for the prompt
        context = {
            "business":    business_name,
            "category":    category,
            "location":    location,
            "title":       summary.get("homepage_title", "Not found"),
            "word_count":  summary.get("homepage_word_count", 0),
            "has_schema":  summary.get("has_schema", False),
            "og_complete": summary.get("og_complete", False),
            "has_sitemap": summary.get("has_sitemap", False),
            "has_robots":  summary.get("has_robots_txt", False),
            "missing_alts": summary.get("images_missing_alt", 0),
            "critical_issues": summary.get("critical_issues", 0),
            "total_issues": summary.get("total_issues", 0),
            "top_issues":  [
                {"severity": i["severity"], "issue": i["issue"]}
                for i in issues
            ],
        }

        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=800,
            temperature=0.6,
            messages=[{
                "role": "user",
                "content": f"""You are an SEO consultant reviewing a website for an Indian business.
Give exactly 5 specific SEO recommendations based on the audit data below.

Business: {business_name} ({category}) in {location}
Audit data: {json.dumps(context, indent=2)}

Rules:
- Focus on what will have the most local SEO impact for an Indian business
- Each recommendation must be specific to THIS business, not generic
- Mention the business name or category in at least 2 recommendations
- Keep language simple — the business owner is not technical

Return ONLY a valid JSON array. No markdown, no explanation, just the JSON:
[
  {{
    "priority": 1,
    "title": "short title (5-8 words)",
    "problem": "what is wrong (1 sentence)",
    "fix": "exactly what to do (1-2 sentences)",
    "impact": "High",
    "service": "which Aidbro service fixes this (e.g. Web Development, Digital Marketing, SEO)"
  }}
]"""
            }]
        )

        raw  = response.choices[0].message.content.strip()
        # Strip markdown code fences if present
        raw  = raw.replace("```json", "").replace("```", "").strip()
        recs = json.loads(raw)

        if isinstance(recs, list) and len(recs) >= 3:
            # Ensure required fields, fill gaps
            cleaned = []
            for i, r in enumerate(recs[:5]):
                cleaned.append({
                    "priority": i + 1,
                    "title":    r.get("title", f"Recommendation {i+1}"),
                    "problem":  r.get("problem", ""),
                    "fix":      r.get("fix", ""),
                    "impact":   r.get("impact", "Medium"),
                    "service":  r.get("service", "Digital Marketing"),
                })
            return cleaned

    except Exception as e:
        print(f"[SEO AI] Groq error: {e}")

    return _fallback_recommendations(seo_data)


def _fallback_recommendations(seo_data: dict) -> list:
    """Hardcoded fallback recommendations when Groq is unavailable."""
    issues  = seo_data.get("issues", [])
    summary = seo_data.get("summary", {})
    recs    = []

    if not summary.get("has_sitemap"):
        recs.append({
            "priority": len(recs) + 1,
            "title":    "Create and submit a sitemap",
            "problem":  "No sitemap.xml found — Google cannot efficiently discover your pages.",
            "fix":      "Generate a sitemap.xml and submit it in Google Search Console.",
            "impact":   "High",
            "service":  "Web Development",
        })

    if not summary.get("has_schema"):
        recs.append({
            "priority": len(recs) + 1,
            "title":    "Add LocalBusiness schema markup",
            "problem":  "No structured data found — Google cannot show rich search results for your business.",
            "fix":      "Add a LocalBusiness JSON-LD schema to your homepage with your name, address, phone, and hours.",
            "impact":   "High",
            "service":  "Web Development",
        })

    if summary.get("images_missing_alt", 0) > 0:
        recs.append({
            "priority": len(recs) + 1,
            "title":    "Fix missing image alt text",
            "problem":  f"{summary['images_missing_alt']} images have no alt text — hurts accessibility and image SEO.",
            "fix":      "Add a short, descriptive alt attribute to every image on your site.",
            "impact":   "Medium",
            "service":  "Web Development",
        })

    if not summary.get("og_complete"):
        recs.append({
            "priority": len(recs) + 1,
            "title":    "Complete Open Graph social tags",
            "problem":  "Missing og:title, og:description, or og:image — your links look unprofessional when shared.",
            "fix":      "Add Open Graph meta tags to every page so social media previews display correctly.",
            "impact":   "Medium",
            "service":  "Web Development",
        })

    if summary.get("homepage_word_count", 300) < 300:
        recs.append({
            "priority": len(recs) + 1,
            "title":    "Add more content to homepage",
            "problem":  f"Homepage has only {summary.get('homepage_word_count', 0)} words — Google treats this as thin content.",
            "fix":      "Expand your homepage with detailed service descriptions, location info, and customer benefits.",
            "impact":   "High",
            "service":  "Digital Marketing",
        })

    # Pad to 5 if fewer
    defaults = [
        {
            "priority": 0,
            "title":    "Build local keyword content",
            "problem":  "Your website doesn't mention your city or area enough for local search.",
            "fix":      "Add location-specific content — mention your city, area, and service keywords naturally.",
            "impact":   "High",
            "service":  "Digital Marketing",
        },
        {
            "priority": 0,
            "title":    "Add a clear contact section",
            "problem":  "Contact information and calls-to-action may not be prominent enough.",
            "fix":      "Add a visible WhatsApp button and phone number to your header and footer.",
            "impact":   "Medium",
            "service":  "Web Development",
        },
    ]

    while len(recs) < 5 and defaults:
        r = defaults.pop(0)
        r["priority"] = len(recs) + 1
        recs.append(r)

    # Renumber
    for i, r in enumerate(recs[:5]):
        r["priority"] = i + 1

    return recs[:5]
