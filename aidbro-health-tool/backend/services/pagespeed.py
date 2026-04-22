import os
import httpx
from urllib.parse import urlparse

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
PSI_BASE = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"


def normalise_url(url: str) -> str:
    """
    Ensure URL has a scheme and is properly formatted.
    This is the single source of truth for URL normalisation —
    both pagespeed and seo_crawler must call this.
    """
    if not url or not url.strip():
        return ""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    # Remove trailing slash for consistency
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")


async def analyze_website(url: str) -> dict:
    """
    Fetch PageSpeed Insights data for a given URL.
    Completely free API — no billing required.
    """
    url = normalise_url(url)
    if not url:
        return _empty_result("No website URL provided")

    try:
        params = {
            "url":      url,
            "strategy": "mobile",
            "category": ["performance", "seo", "accessibility", "best-practices"],
        }
        if GOOGLE_API_KEY and GOOGLE_API_KEY != "your_google_key_here":
            params["key"] = GOOGLE_API_KEY

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(PSI_BASE, params=params)
            data     = response.json()

        if "error" in data or "lighthouseResult" not in data:
            return _empty_result(f"PageSpeed check failed: {data.get('error', {}).get('message', 'unknown')}")

        lh         = data["lighthouseResult"]
        categories = lh.get("categories", {})
        audits     = lh.get("audits", {})

        def score(key: str) -> int:
            val = categories.get(key, {}).get("score")
            return round(val * 100) if val is not None else 0

        def audit_val(key: str) -> str:
            return audits.get(key, {}).get("displayValue", "N/A")

        is_https = url.startswith("https://")

        lcp_str = audit_val("largest-contentful-paint")
        try:
            lcp_secs = float(lcp_str.replace(" s", "").replace("s", "").strip())
            fast_load = lcp_secs <= 3.0
        except Exception:
            fast_load = False

        return {
            "found":               True,
            "url":                 url,
            "is_https":            is_https,
            "performance_score":   score("performance"),
            "seo_score":           score("seo"),
            "accessibility_score": score("accessibility"),
            "best_practices_score":score("best-practices"),
            "lcp":                 lcp_str,
            "cls":                 audit_val("cumulative-layout-shift"),
            "fcp":                 audit_val("first-contentful-paint"),
            "speed_index":         audit_val("speed-index"),
            "mobile_friendly":     score("performance") >= 50,
            "fast_load":           fast_load,
            "error":               None,
        }

    except Exception as e:
        print(f"[PageSpeed] Error for {url}: {e}")
        return _empty_result(str(e))


def _empty_result(reason: str) -> dict:
    return {
        "found":               False,
        "url":                 "",
        "is_https":            False,
        "performance_score":   0,
        "seo_score":           0,
        "accessibility_score": 0,
        "best_practices_score":0,
        "lcp":                 "N/A",
        "cls":                 "N/A",
        "fcp":                 "N/A",
        "speed_index":         "N/A",
        "mobile_friendly":     False,
        "fast_load":           False,
        "error":               reason,
    }
