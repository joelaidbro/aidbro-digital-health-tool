import re

import httpx


EMAIL_PATTERN = re.compile(r"[\w.\-+%]+@[\w.\-]+\.[A-Za-z]{2,}")


async def discover_contact_email(website_url: str) -> str:
    """
    Best-effort contact email discovery from the website homepage.
    This is a fallback for cases where Google Places has phone data but no email.
    """
    if not website_url:
        return ""

    try:
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            response = await client.get(website_url)
            html = response.text or ""
    except Exception:
        return ""

    mailto_match = re.search(r"mailto:([^\"'>\s]+)", html, flags=re.IGNORECASE)
    if mailto_match:
        return mailto_match.group(1).strip()

    email_match = EMAIL_PATTERN.search(html)
    if email_match:
        return email_match.group(0).strip()

    return ""
