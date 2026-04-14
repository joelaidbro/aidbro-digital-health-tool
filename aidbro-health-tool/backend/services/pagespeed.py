import os
import httpx

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
PSI_BASE = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"


async def analyze_website(url: str) -> dict:
    """
    Fetch PageSpeed Insights data for a given URL.
    This API is free and works without billing.
    Returns scores for Performance, SEO, Accessibility + key metrics.
    """
    if not url:
        return _empty_result("No website URL provided")

    # Ensure URL has a scheme
    if not url.startswith("http"):
        url = "https://" + url

    try:
        params = {
            "url": url,
            "strategy": "mobile",
            "category": ["performance", "seo", "accessibility", "best-practices"],
        }
        if GOOGLE_API_KEY and GOOGLE_API_KEY != "your_google_key_here":
            params["key"] = GOOGLE_API_KEY

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(PSI_BASE, params=params)
            data = response.json()

        if "lighthouseResult" not in data:
            return _empty_result("PageSpeed check failed")

        lh = data["lighthouseResult"]
        categories = lh.get("categories", {})
        audits = lh.get("audits", {})

        def score(cat_key: str) -> int:
            cat = categories.get(cat_key, {})
            val = cat.get("score")
            return round(val * 100) if val is not None else 0

        def audit_val(key: str) -> str:
            return audits.get(key, {}).get("displayValue", "N/A")

        # Check for HTTPS
        is_https = url.startswith("https://")

        # Check for basic contact signals in the meta tags or audit descriptions
        has_structured = audits.get("structured-data", {}).get("score", 0) == 1

        result = {
            "found": True,
            "url": url,
            "is_https": is_https,
            "performance_score": score("performance"),
            "seo_score": score("seo"),
            "accessibility_score": score("accessibility"),
            "best_practices_score": score("best-practices"),
            "lcp": audit_val("largest-contentful-paint"),
            "cls": audit_val("cumulative-layout-shift"),
            "fcp": audit_val("first-contentful-paint"),
            "speed_index": audit_val("speed-index"),
            "has_structured_data": has_structured,
            "mobile_friendly": score("performance") >= 50,
        }

        # Determine load speed bucket
        lcp_str = result["lcp"]
        try:
            lcp_seconds = float(lcp_str.replace("s", "").replace(" s", "").strip())
            result["fast_load"] = lcp_seconds <= 3.0
        except Exception:
            result["fast_load"] = False

        return result

    except Exception as e:
        print(f"[PageSpeed] Error for {url}: {e}")
        return _empty_result(str(e))


def _empty_result(reason: str) -> dict:
    return {
        "found": False,
        "url": "",
        "is_https": False,
        "performance_score": 0,
        "seo_score": 0,
        "accessibility_score": 0,
        "best_practices_score": 0,
        "lcp": "N/A",
        "cls": "N/A",
        "fcp": "N/A",
        "speed_index": "N/A",
        "has_structured_data": False,
        "mobile_friendly": False,
        "fast_load": False,
        "error": reason,
    }