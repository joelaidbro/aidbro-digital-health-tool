import re
import httpx

SOCIAL_PATTERNS = {
    "facebook":  [r'facebook\.com/(?!sharer|share|dialog|login)[a-zA-Z0-9._/-]+'],
    "instagram": [r'instagram\.com/[a-zA-Z0-9._/-]+'],
    "youtube":   [r'youtube\.com/(?:channel|c|user|@)[a-zA-Z0-9._/-]+'],
    "linkedin":  [r'linkedin\.com/(?:company|in)/[a-zA-Z0-9._/-]+'],
    "twitter":   [r'twitter\.com/[a-zA-Z0-9_]+', r'x\.com/[a-zA-Z0-9_]+'],
    "whatsapp":  [r'wa\.me/[0-9]+', r'whatsapp\.com/send', r'api\.whatsapp\.com'],
}


async def check_social_presence(
    website_url: str,
    google_data: dict,
    manual_socials: dict = None,
) -> dict:
    """
    Detect social media presence.
    Priority: manual handles provided by user > auto-detection from website HTML.
    """
    if manual_socials is None:
        manual_socials = {}

    result = {
        "facebook":            False,
        "instagram":           False,
        "youtube":             False,
        "linkedin":            False,
        "twitter":             False,
        "whatsapp_business":   False,
        "social_links_on_website": False,
        "found_platforms":     [],
        "social_count":        0,
        "website_scraped":     False,
        # Store which ones came from manual input vs auto-detection
        "manual_verified":     [],
        "auto_detected":       [],
    }

    # ── 1. Manual handles (highest confidence) ────────────────────────────────
    if manual_socials.get("instagram_url", "").strip():
        result["instagram"] = True
        result["manual_verified"].append("instagram")

    if manual_socials.get("facebook_url", "").strip():
        result["facebook"] = True
        result["manual_verified"].append("facebook")

    if manual_socials.get("linkedin_url", "").strip():
        result["linkedin"] = True
        result["manual_verified"].append("linkedin")

    if manual_socials.get("youtube_url", "").strip():
        result["youtube"] = True
        result["manual_verified"].append("youtube")

    if manual_socials.get("twitter_url", "").strip():
        result["twitter"] = True
        result["manual_verified"].append("twitter")

    # ── 2. WhatsApp from phone number (Indian mobile) ─────────────────────────
    phone = google_data.get("phone", "")
    if phone:
        clean = re.sub(r"[^0-9]", "", phone)
        if len(clean) >= 10:
            result["whatsapp_business"] = True
            result["auto_detected"].append("whatsapp_business")

    # ── 3. Auto-detect remaining platforms by scraping website ────────────────
    if website_url:
        if not website_url.startswith("http"):
            website_url = "https://" + website_url
        try:
            async with httpx.AsyncClient(
                timeout=10.0,
                follow_redirects=True,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
                    )
                },
            ) as client:
                response = await client.get(website_url)
                html = response.text
                result["website_scraped"] = True
        except Exception as e:
            print(f"[Social] Scrape failed for {website_url}: {e}")
            html = ""

        for platform, patterns in SOCIAL_PATTERNS.items():
            # Skip platforms already confirmed via manual input
            if result.get(platform):
                continue
            for pattern in patterns:
                if re.search(pattern, html, re.IGNORECASE):
                    result[platform] = True
                    if platform not in result["auto_detected"]:
                        result["auto_detected"].append(platform)
                    break

    # ── 4. Build summary fields ───────────────────────────────────────────────
    all_platforms = [
        "facebook", "instagram", "youtube",
        "linkedin", "twitter", "whatsapp_business"
    ]
    result["found_platforms"]       = [p for p in all_platforms if result.get(p)]
    result["social_links_on_website"] = len(result["auto_detected"]) > 0
    result["social_count"]          = len(result["found_platforms"])

    return result
