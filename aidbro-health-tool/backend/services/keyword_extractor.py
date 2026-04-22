"""
Keyword Intent Extractor
=========================
Extracts intended SEO keywords from website content using AI.
This shows keyword STRATEGY, not actual rankings.
Always label output as "Keyword Strategy Analysis" not "Rankings".

Phase 2A: AI intent extraction from page content (free)
Phase 3:  Real rankings via DataForSEO API (paid upgrade)
"""

import os
import json
import asyncio
import httpx
import re
from bs4 import BeautifulSoup
from groq import Groq

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    )
}


async def extract_keywords(
    business_name: str,
    category: str,
    location: str,
    target_url: str,
    competitor_urls: list,
) -> dict:
    """
    Extract keyword strategies from target + competitor websites.

    Returns:
    {
      "your_keywords":         list of keyword objects,
      "competitor_keywords":   list of keyword objects,
      "missing_keywords":      list of keyword objects (in competitors, not in yours),
      "shared_keywords":       list of strings,
      "ai_analysis":           str,
      "disclaimer":            str,
      "is_mocked":             bool,
    }
    """
    # ── Fetch page content for target ─────────────────────────────────────────
    target_content  = await _fetch_page_content(target_url) if target_url else {}
    comp_urls_clean = [u for u in competitor_urls if u][:3]  # max 3 competitors

    # ── Fetch competitor content in parallel ──────────────────────────────────
    if comp_urls_clean:
        comp_contents = await asyncio.gather(
            *[_fetch_page_content(u) for u in comp_urls_clean],
            return_exceptions=True
        )
        comp_contents = [c for c in comp_contents if isinstance(c, dict)]
    else:
        comp_contents = []

    # ── Extract keywords via AI ───────────────────────────────────────────────
    your_keywords  = _extract_with_ai(
        business_name, category, location, target_content, "target"
    ) if target_content else []

    comp_keywords  = []
    for content in comp_contents:
        kws = _extract_with_ai(
            content.get("domain", "competitor"), category, location, content, "competitor"
        )
        comp_keywords.extend(kws)

    # Deduplicate competitor keywords
    seen = set()
    unique_comp_kws = []
    for kw in comp_keywords:
        key = kw["keyword"].lower()
        if key not in seen:
            seen.add(key)
            unique_comp_kws.append(kw)

    # ── Gap analysis ──────────────────────────────────────────────────────────
    your_kw_set  = {k["keyword"].lower() for k in your_keywords}
    comp_kw_set  = {k["keyword"].lower() for k in unique_comp_kws}

    missing = [
        kw for kw in unique_comp_kws
        if kw["keyword"].lower() not in your_kw_set
    ]
    shared  = list(your_kw_set & comp_kw_set)[:10]

    # ── AI analysis paragraph ─────────────────────────────────────────────────
    ai_analysis = _generate_keyword_analysis(
        business_name, category, location,
        your_keywords, unique_comp_kws, missing
    )

    is_mocked = not bool(target_url)

    return {
        "your_keywords":       your_keywords[:12],
        "competitor_keywords": unique_comp_kws[:15],
        "missing_keywords":    missing[:8],
        "shared_keywords":     shared,
        "ai_analysis":         ai_analysis,
        "disclaimer":          (
            "⚠️ This shows keyword strategy based on website content analysis — "
            "not actual Google search rankings. Upgrade to Detailed Audit for real ranking data."
        ),
        "is_mocked": is_mocked,
    }


async def _fetch_page_content(url: str) -> dict:
    """Fetch a page and extract SEO-relevant text content."""
    if not url:
        return {}
    if not url.startswith("http"):
        url = "https://" + url

    try:
        async with httpx.AsyncClient(
            timeout=10.0,
            follow_redirects=True,
            headers=HEADERS,
        ) as client:
            response = await client.get(url)
            if response.status_code != 200:
                return {}

        soup = BeautifulSoup(response.text, "lxml")

        # Remove noise
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        # Extract structured text
        title       = soup.find("title")
        meta_desc   = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
        h1s = [h.get_text(strip=True) for h in soup.find_all("h1")]
        h2s = [h.get_text(strip=True) for h in soup.find_all("h2")][:6]
        h3s = [h.get_text(strip=True) for h in soup.find_all("h3")][:6]
        body_text   = soup.get_text(separator=" ", strip=True)[:1500]

        from urllib.parse import urlparse
        domain = urlparse(url).netloc

        return {
            "url":         url,
            "domain":      domain,
            "title":       title.string.strip() if title and title.string else "",
            "meta_desc":   meta_desc["content"].strip() if meta_desc and meta_desc.get("content") else "",
            "h1":          h1s[:2],
            "h2":          h2s,
            "h3":          h3s,
            "body":        body_text,
        }

    except Exception as e:
        print(f"[Keywords] Fetch error for {url}: {e}")
        return {}


def _extract_with_ai(
    name: str,
    category: str,
    location: str,
    content: dict,
    role: str,
) -> list:
    """Extract top keywords from page content using Groq."""
    if not content:
        return _fallback_keywords(category, location)

    if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_key_here":
        return _fallback_keywords(category, location)

    try:
        context = {
            "title":     content.get("title", ""),
            "meta_desc": content.get("meta_desc", ""),
            "headings":  content.get("h1", []) + content.get("h2", []) + content.get("h3", []),
            "body":      content.get("body", "")[:800],
        }

        client   = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=400,
            temperature=0.4,
            messages=[{
                "role": "user",
                "content": f"""Extract the top 8-10 SEO keywords this {category} business in {location} is targeting.
Focus on commercial intent keywords a customer would search.
Include local keywords (with location) where relevant.

Website content:
Title: {context['title']}
Meta: {context['meta_desc']}
Headings: {', '.join(context['headings'][:8])}
Body excerpt: {context['body'][:500]}

Return ONLY valid JSON array, no markdown:
[{{"keyword": "...", "intent": "local|service|product|brand", "relevance": "high|medium|low"}}]"""
            }]
        )

        raw  = response.choices[0].message.content.strip()
        raw  = raw.replace("```json", "").replace("```", "").strip()
        kws  = json.loads(raw)

        if isinstance(kws, list):
            return [
                {
                    "keyword":   k.get("keyword", ""),
                    "intent":    k.get("intent", "service"),
                    "relevance": k.get("relevance", "medium"),
                }
                for k in kws[:12]
                if k.get("keyword")
            ]

    except Exception as e:
        print(f"[Keywords] AI error: {e}")

    return _fallback_keywords(category, location)


def _generate_keyword_analysis(
    business_name: str,
    category: str,
    location: str,
    your_keywords: list,
    comp_keywords: list,
    missing: list,
) -> str:
    """Generate a 2-3 sentence keyword strategy analysis."""
    if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_key_here":
        return _fallback_analysis(business_name, missing)

    try:
        your_top  = [k["keyword"] for k in your_keywords[:5]]
        miss_top  = [k["keyword"] for k in missing[:5]]

        if not miss_top:
            return (
                f"{business_name} covers similar keyword themes to local competitors. "
                f"Focus on creating more location-specific content to strengthen local search dominance."
            )

        client   = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=100,
            temperature=0.5,
            messages=[{
                "role": "user",
                "content": f"""Write 2 sentences about the keyword strategy gap for {business_name} ({category}, {location}).

Their keywords: {', '.join(your_top)}
Missing keywords (competitors have, they don't): {', '.join(miss_top)}

Be specific and practical. Tell them what they're missing and why it matters."""
            }]
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"[Keywords] Analysis AI error: {e}")
        return _fallback_analysis(business_name, missing)


def _fallback_keywords(category: str, location: str) -> list:
    """Return sensible fallback keywords when AI is unavailable."""
    city = location.split(",")[0].strip()
    return [
        {"keyword": f"{category} in {city}",         "intent": "local",   "relevance": "high"},
        {"keyword": f"best {category} {city}",        "intent": "local",   "relevance": "high"},
        {"keyword": f"{category} near me",            "intent": "local",   "relevance": "high"},
        {"keyword": f"affordable {category} {city}",  "intent": "service", "relevance": "medium"},
        {"keyword": f"{category} services",           "intent": "service", "relevance": "medium"},
        {"keyword": f"top {category} Kerala",         "intent": "local",   "relevance": "medium"},
    ]


def _fallback_analysis(business_name: str, missing: list) -> str:
    if not missing:
        return (
            f"{business_name}'s website covers similar keyword themes to local competitors. "
            "Adding more location-specific content can help capture searches competitors are targeting."
        )
    miss_top = [k["keyword"] for k in missing[:3]]
    return (
        f"{business_name}'s website is not targeting keywords like '{miss_top[0]}' "
        f"that local competitors rank for. "
        f"Adding this content to your website and service pages could bring in new organic traffic."
    )
