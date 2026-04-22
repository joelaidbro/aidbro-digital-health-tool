"""
SEO Site Audit Crawler
=======================
Crawls a business website and produces a detailed on-page SEO report.

Free tool (Stage 2):  Homepage only
Stage 4 premium:      Full site crawl up to 50 pages

Checks performed per page:
  Title tag, meta description, H1/H2/H3 structure,
  images alt text, word count, canonical, Open Graph,
  schema markup, internal/external links, page speed

Site-level checks:
  robots.txt, sitemap.xml, HTTPS everywhere,
  broken internal links, duplicate titles/metas,
  viewport meta tag
"""

import asyncio
import re
import time
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup


# ── Constants ─────────────────────────────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
}
TIMEOUT   = 12.0   # seconds per request
MAX_PAGES = 8      # free tier crawl limit (homepage + up to 7 inner pages)
MAX_PAGES_PREMIUM = 50


# ── Main entry point ──────────────────────────────────────────────────────────

async def crawl_website(
    url: str,
    premium: bool = False,
) -> dict:
    """
    Crawl a website and return a structured SEO audit.

    Args:
        url:     Website URL to audit
        premium: If True, crawl up to 50 pages. Otherwise homepage only + 7 inner pages.

    Returns:
        {
          "url":         str,
          "pages":       list of per-page results,
          "site_level":  dict of site-wide checks,
          "score":       int (0-30 points for Pillar 2 additions),
          "checks":      list of scored check objects (for scorer integration),
          "issues":      list of all issues found,
          "summary":     dict of key metrics,
        }
    """
    if not url:
        return _empty_result("No URL provided")

    if not url.startswith("http"):
        url = "https://" + url

    # Normalise base URL
    parsed  = urlparse(url)
    base    = f"{parsed.scheme}://{parsed.netloc}"
    max_pgs = MAX_PAGES_PREMIUM if premium else MAX_PAGES

    try:
        async with httpx.AsyncClient(
            timeout=TIMEOUT,
            follow_redirects=True,
            headers=HEADERS,
        ) as client:

            # ── Step 1: Crawl homepage ────────────────────────────────────────
            homepage_result = await _crawl_page(client, url, base)
            pages = [homepage_result]

            # ── Step 2: Discover inner pages from homepage links ──────────────
            if homepage_result.get("internal_link_urls") and max_pgs > 1:
                inner_urls = homepage_result["internal_link_urls"][: max_pgs - 1]
                inner_tasks = [
                    _crawl_page(client, inner_url, base)
                    for inner_url in inner_urls
                ]
                inner_results = await asyncio.gather(*inner_tasks, return_exceptions=True)
                for r in inner_results:
                    if isinstance(r, dict):
                        pages.append(r)

            # ── Step 3: Site-level checks ─────────────────────────────────────
            site_level = await _site_level_checks(client, base, pages)

    except Exception as e:
        print(f"[SEO Crawler] Fatal error for {url}: {e}")
        return _empty_result(str(e))

    # ── Step 4: Build scored checks for scorer.py integration ────────────────
    checks, score = _build_scored_checks(pages, site_level)

    # ── Step 5: Collect all issues ────────────────────────────────────────────
    issues = _collect_issues(pages, site_level)

    # ── Step 6: Summary metrics ───────────────────────────────────────────────
    summary = _build_summary(pages, site_level, issues)

    return {
        "url":        url,
        "pages":      [_clean_page(p) for p in pages],
        "site_level": site_level,
        "score":      score,
        "checks":     checks,
        "issues":     issues,
        "summary":    summary,
        "error":      None,
    }


# ── Per-page crawl ────────────────────────────────────────────────────────────

async def _crawl_page(
    client: httpx.AsyncClient,
    url: str,
    base: str,
) -> dict:
    """Crawl a single page and extract all SEO signals."""
    result = {
        "url":                    url,
        "status_code":            None,
        "load_time_ms":           None,
        "error":                  None,
        # Title
        "title":                  None,
        "title_length":           0,
        "title_ok":               False,
        # Meta description
        "meta_description":       None,
        "meta_desc_length":       0,
        "meta_desc_ok":           False,
        # Headings
        "h1_count":               0,
        "h1_text":                None,
        "h1_ok":                  False,
        "h2_count":               0,
        "h3_count":               0,
        "heading_structure_ok":   False,
        # Content
        "word_count":             0,
        "is_thin_content":        False,
        # Images
        "images_total":           0,
        "images_missing_alt":     0,
        "images_alt_ok":          False,
        # Links
        "internal_links":         0,
        "external_links":         0,
        "internal_link_urls":     [],
        "broken_links":           [],
        # Technical
        "has_canonical":          False,
        "canonical_url":          None,
        "has_og_title":           False,
        "has_og_description":     False,
        "has_og_image":           False,
        "og_complete":            False,
        "has_schema_markup":      False,
        "schema_types":           [],
        "has_viewport":           False,
        "is_https":               url.startswith("https://"),
    }

    try:
        t0 = time.monotonic()
        response = await client.get(url)
        result["load_time_ms"] = round((time.monotonic() - t0) * 1000)
        result["status_code"]  = response.status_code

        if response.status_code != 200:
            result["error"] = f"HTTP {response.status_code}"
            return result

        soup = BeautifulSoup(response.text, "lxml")

        # ── Title ─────────────────────────────────────────────────────────────
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            title = title_tag.string.strip()
            result["title"]        = title
            result["title_length"] = len(title)
            result["title_ok"]     = 30 <= len(title) <= 65

        # ── Meta description ──────────────────────────────────────────────────
        meta_desc = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
        if meta_desc and meta_desc.get("content"):
            desc = meta_desc["content"].strip()
            result["meta_description"] = desc
            result["meta_desc_length"] = len(desc)
            result["meta_desc_ok"]     = 120 <= len(desc) <= 165

        # ── Headings ──────────────────────────────────────────────────────────
        h1s = soup.find_all("h1")
        h2s = soup.find_all("h2")
        h3s = soup.find_all("h3")
        result["h1_count"] = len(h1s)
        result["h2_count"] = len(h2s)
        result["h3_count"] = len(h3s)
        if h1s:
            result["h1_text"] = h1s[0].get_text(strip=True)[:200]
        result["h1_ok"]               = len(h1s) == 1
        result["heading_structure_ok"] = len(h1s) == 1 and len(h2s) >= 1

        # ── Word count ────────────────────────────────────────────────────────
        # Remove scripts/styles before counting
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        body_text  = soup.get_text(separator=" ", strip=True)
        word_count = len(body_text.split())
        result["word_count"]      = word_count
        result["is_thin_content"] = word_count < 300

        # ── Images ────────────────────────────────────────────────────────────
        images = soup.find_all("img")
        missing_alt = sum(
            1 for img in images
            if not img.get("alt") or img.get("alt", "").strip() == ""
        )
        result["images_total"]       = len(images)
        result["images_missing_alt"] = missing_alt
        result["images_alt_ok"]      = missing_alt == 0 and len(images) > 0

        # ── Links ─────────────────────────────────────────────────────────────
        internal_urls = []
        ext_count     = 0
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue
            full_url = urljoin(base, href)
            if urlparse(full_url).netloc == urlparse(base).netloc:
                clean = full_url.split("#")[0].rstrip("/")
                if clean and clean != url.rstrip("/"):
                    internal_urls.append(clean)
            else:
                ext_count += 1

        # Deduplicate and limit
        seen = set()
        unique_internal = []
        for u in internal_urls:
            if u not in seen:
                seen.add(u)
                unique_internal.append(u)

        result["internal_links"]     = len(unique_internal)
        result["external_links"]     = ext_count
        result["internal_link_urls"] = unique_internal[:20]  # cap for crawling

        # ── Canonical ─────────────────────────────────────────────────────────
        canonical = soup.find("link", rel=re.compile("canonical", re.I))
        if canonical and canonical.get("href"):
            result["has_canonical"] = True
            result["canonical_url"] = canonical["href"]

        # ── Open Graph ────────────────────────────────────────────────────────
        og_title = soup.find("meta", property="og:title")
        og_desc  = soup.find("meta", property="og:description")
        og_img   = soup.find("meta", property="og:image")
        result["has_og_title"]       = bool(og_title and og_title.get("content"))
        result["has_og_description"] = bool(og_desc  and og_desc.get("content"))
        result["has_og_image"]       = bool(og_img   and og_img.get("content"))
        result["og_complete"] = all([
            result["has_og_title"],
            result["has_og_description"],
            result["has_og_image"],
        ])

        # ── Schema markup ─────────────────────────────────────────────────────
        schema_scripts = soup.find_all("script", type="application/ld+json")
        schema_types   = []
        for s in schema_scripts:
            try:
                import json
                data = json.loads(s.string or "")
                if isinstance(data, dict) and "@type" in data:
                    schema_types.append(data["@type"])
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "@type" in item:
                            schema_types.append(item["@type"])
            except Exception:
                pass
        result["has_schema_markup"] = len(schema_types) > 0
        result["schema_types"]      = schema_types

        # ── Viewport ──────────────────────────────────────────────────────────
        viewport = soup.find("meta", attrs={"name": re.compile("viewport", re.I)})
        result["has_viewport"] = bool(viewport)

    except httpx.TimeoutException:
        result["error"] = "Page timed out"
    except Exception as e:
        result["error"] = str(e)[:100]

    return result


# ── Site-level checks ─────────────────────────────────────────────────────────

async def _site_level_checks(
    client: httpx.AsyncClient,
    base: str,
    pages: list,
) -> dict:
    """Run checks that apply to the entire site, not individual pages."""
    result = {
        "has_robots_txt":      False,
        "robots_txt_url":      f"{base}/robots.txt",
        "has_sitemap":         False,
        "sitemap_url":         None,
        "all_pages_https":     False,
        "broken_internal_links": [],
        "duplicate_titles":    [],
        "duplicate_meta_descs": [],
        "has_viewport":        False,
    }

    # ── robots.txt ────────────────────────────────────────────────────────────
    try:
        r = await client.get(f"{base}/robots.txt")
        if r.status_code == 200 and "user-agent" in r.text.lower():
            result["has_robots_txt"] = True
            # Check for sitemap in robots.txt
            for line in r.text.splitlines():
                if line.lower().startswith("sitemap:"):
                    result["sitemap_url"]  = line.split(":", 1)[1].strip()
                    result["has_sitemap"]  = True
                    break
    except Exception:
        pass

    # ── sitemap.xml (fallback check) ──────────────────────────────────────────
    if not result["has_sitemap"]:
        for path in ["/sitemap.xml", "/sitemap_index.xml", "/sitemap/"]:
            try:
                r = await client.get(f"{base}{path}")
                if r.status_code == 200 and (
                    "urlset" in r.text or "sitemapindex" in r.text
                ):
                    result["has_sitemap"] = True
                    result["sitemap_url"] = f"{base}{path}"
                    break
            except Exception:
                pass

    # ── HTTPS everywhere ──────────────────────────────────────────────────────
    result["all_pages_https"] = all(
        p.get("is_https", False) for p in pages if not p.get("error")
    )

    # ── Duplicate titles ──────────────────────────────────────────────────────
    seen_titles: dict[str, list] = {}
    for p in pages:
        t = p.get("title")
        if t:
            seen_titles.setdefault(t, []).append(p["url"])
    result["duplicate_titles"] = [
        {"title": t, "urls": urls}
        for t, urls in seen_titles.items()
        if len(urls) > 1
    ]

    # ── Duplicate meta descriptions ───────────────────────────────────────────
    seen_metas: dict[str, list] = {}
    for p in pages:
        m = p.get("meta_description")
        if m:
            seen_metas.setdefault(m, []).append(p["url"])
    result["duplicate_meta_descs"] = [
        {"description": m[:80] + "...", "urls": urls}
        for m, urls in seen_metas.items()
        if len(urls) > 1
    ]

    # ── Viewport (site-level: does homepage have it) ──────────────────────────
    if pages:
        result["has_viewport"] = pages[0].get("has_viewport", False)

    # ── Check broken internal links from homepage ─────────────────────────────
    if pages and pages[0].get("internal_link_urls"):
        broken = []
        check_urls = pages[0]["internal_link_urls"][:5]  # check up to 5
        for link_url in check_urls:
            try:
                r = await client.head(link_url)
                if r.status_code in (404, 410):
                    broken.append({"url": link_url, "status": r.status_code})
            except Exception:
                pass
        result["broken_internal_links"] = broken

    return result


# ── Score builder ─────────────────────────────────────────────────────────────

def _build_scored_checks(pages: list, site_level: dict) -> tuple[list, int]:
    """
    Build a list of scored check objects compatible with scorer.py format.
    These are added to Pillar 2 (Website Quality) when SEO crawler runs.
    Returns (checks_list, total_points).
    """
    hp = pages[0] if pages else {}
    checks = []

    def chk(name, passed, pts, fail_msg, fix, service="Digital Marketing / SEO"):
        return {
            "check":         name,
            "passed":        passed,
            "points_earned": pts if passed else 0,
            "points_max":    pts,
            "value":         "✓" if passed else "✗",
            "message":       (f"{name} looks good." if passed else fail_msg),
            "fix":           fix,
            "service":       service,
            "skipped":       False,
        }

    # robots.txt
    checks.append(chk(
        "robots.txt present",
        site_level.get("has_robots_txt", False), 1,
        "No robots.txt — search engines don't have crawling instructions.",
        "Create a robots.txt at yourdomain.com/robots.txt"
    ))

    # sitemap.xml
    checks.append(chk(
        "sitemap.xml present",
        site_level.get("has_sitemap", False), 1,
        "No sitemap — Google can't efficiently discover all your pages.",
        "Generate a sitemap.xml and submit it in Google Search Console."
    ))

    # No broken links
    no_broken = len(site_level.get("broken_internal_links", [])) == 0
    checks.append(chk(
        "No broken internal links",
        no_broken, 2,
        f"{len(site_level.get('broken_internal_links', []))} broken link(s) found — bad for SEO and user experience.",
        "Fix or remove all internal links returning 404 errors."
    ))

    # H1 structure
    checks.append(chk(
        "Correct H1 heading structure",
        hp.get("h1_ok", False), 2,
        f"H1 issues: found {hp.get('h1_count', 0)} H1 tag(s) — exactly 1 is required.",
        "Ensure every page has exactly one H1 tag describing the page content.",
        "Web Development"
    ))

    # All images have alt text
    checks.append(chk(
        "All images have alt text",
        hp.get("images_alt_ok", False) or hp.get("images_total", 0) == 0, 1,
        f"{hp.get('images_missing_alt', 0)} image(s) missing alt text — hurts accessibility and image SEO.",
        "Add descriptive alt text to all images.",
        "Web Development"
    ))

    # Open Graph tags complete
    checks.append(chk(
        "Open Graph tags complete",
        hp.get("og_complete", False), 1,
        "Missing og:title, og:description, or og:image — links shared on social media won't preview properly.",
        "Add og:title, og:description, and og:image meta tags to every page.",
        "Web Development"
    ))

    # Schema markup
    checks.append(chk(
        "Schema / structured data present",
        hp.get("has_schema_markup", False), 2,
        "No schema markup found — Google can't show rich results for your business.",
        "Add LocalBusiness schema JSON-LD to your homepage.",
        "Web Development"
    ))

    # Meta description
    checks.append(chk(
        "Meta description present and optimal length",
        hp.get("meta_desc_ok", False), 1,
        f"Meta description is {hp.get('meta_desc_length', 0)} chars — ideal is 120–165 chars.",
        "Write a compelling meta description between 120–165 characters for the homepage.",
        "Digital Marketing"
    ))

    # Title tag
    checks.append(chk(
        "Title tag present and optimal length",
        hp.get("title_ok", False), 1,
        f"Title is {hp.get('title_length', 0)} chars — ideal is 30–65 chars.",
        "Write a concise, keyword-rich title tag between 30–65 characters.",
        "Digital Marketing"
    ))

    # No thin content
    checks.append(chk(
        "Sufficient page content (300+ words)",
        not hp.get("is_thin_content", True), 1,
        f"Only {hp.get('word_count', 0)} words on homepage — Google considers this thin content.",
        "Add more detailed content about your services, location, and value proposition.",
        "Digital Marketing"
    ))

    total_pts = sum(c["points_earned"] for c in checks)
    return checks, total_pts


# ── Issues collector ──────────────────────────────────────────────────────────

def _collect_issues(pages: list, site_level: dict) -> list:
    """Build a flat list of all issues for the report's issues section."""
    issues = []

    def add(severity, category, issue, fix, url=None):
        issues.append({
            "severity": severity,   # critical | warning | info
            "category": category,
            "issue":    issue,
            "fix":      fix,
            "url":      url,
        })

    hp = pages[0] if pages else {}

    # Site-level issues
    if not site_level.get("has_robots_txt"):
        add("warning", "Technical SEO", "robots.txt missing",
            "Create /robots.txt with crawling instructions")
    if not site_level.get("has_sitemap"):
        add("warning", "Technical SEO", "sitemap.xml missing",
            "Generate sitemap and submit to Google Search Console")
    if not site_level.get("all_pages_https"):
        add("critical", "Security", "Not all pages use HTTPS",
            "Install SSL certificate and redirect all HTTP to HTTPS")
    for bl in site_level.get("broken_internal_links", []):
        add("critical", "Links", f"Broken link: {bl['url']} ({bl['status']})",
            "Fix or remove this broken link", bl["url"])
    for dt in site_level.get("duplicate_titles", []):
        add("warning", "Content", f"Duplicate title tag across {len(dt['urls'])} pages",
            "Write unique title tags for each page")

    # Homepage issues
    if not hp.get("title_ok"):
        length = hp.get("title_length", 0)
        msg = "Title tag missing" if length == 0 else f"Title too {'short' if length < 30 else 'long'} ({length} chars)"
        add("critical", "On-Page SEO", msg, "Write a 30–65 character title tag", hp.get("url"))
    if not hp.get("meta_desc_ok"):
        add("warning", "On-Page SEO",
            f"Meta description {hp.get('meta_desc_length', 0)} chars (ideal: 120–165)",
            "Write a 120–165 character meta description", hp.get("url"))
    if not hp.get("h1_ok"):
        add("critical", "On-Page SEO",
            f"Found {hp.get('h1_count', 0)} H1 tags (exactly 1 required)",
            "Use exactly one H1 tag per page", hp.get("url"))
    if hp.get("images_missing_alt", 0) > 0:
        add("warning", "Accessibility",
            f"{hp.get('images_missing_alt')} images missing alt text",
            "Add descriptive alt text to all images", hp.get("url"))
    if hp.get("is_thin_content"):
        add("warning", "Content",
            f"Homepage has only {hp.get('word_count', 0)} words (minimum: 300)",
            "Add more detailed service and location content", hp.get("url"))
    if not hp.get("og_complete"):
        add("info", "Social Sharing",
            "Open Graph tags incomplete — poor social media preview",
            "Add og:title, og:description, and og:image", hp.get("url"))
    if not hp.get("has_schema_markup"):
        add("info", "Structured Data",
            "No schema markup found",
            "Add LocalBusiness schema JSON-LD", hp.get("url"))
    if not hp.get("has_canonical"):
        add("info", "Technical SEO",
            "No canonical tag on homepage",
            "Add <link rel='canonical' href='...'> to avoid duplicate content", hp.get("url"))

    # Sort by severity
    order = {"critical": 0, "warning": 1, "info": 2}
    issues.sort(key=lambda x: order.get(x["severity"], 3))

    return issues


# ── Summary builder ───────────────────────────────────────────────────────────

def _build_summary(pages: list, site_level: dict, issues: list) -> dict:
    hp = pages[0] if pages else {}
    return {
        "pages_crawled":          len(pages),
        "total_issues":           len(issues),
        "critical_issues":        sum(1 for i in issues if i["severity"] == "critical"),
        "warning_issues":         sum(1 for i in issues if i["severity"] == "warning"),
        "has_robots_txt":         site_level.get("has_robots_txt", False),
        "has_sitemap":            site_level.get("has_sitemap", False),
        "homepage_title":         hp.get("title"),
        "homepage_word_count":    hp.get("word_count", 0),
        "homepage_h1":            hp.get("h1_text"),
        "images_missing_alt":     hp.get("images_missing_alt", 0),
        "has_schema":             hp.get("has_schema_markup", False),
        "schema_types":           hp.get("schema_types", []),
        "og_complete":            hp.get("og_complete", False),
        "load_time_ms":           hp.get("load_time_ms"),
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _clean_page(page: dict) -> dict:
    """Remove internal fields not needed by frontend."""
    p = dict(page)
    p.pop("internal_link_urls", None)
    return p


def _empty_result(reason: str) -> dict:
    return {
        "url":        "",
        "pages":      [],
        "site_level": {},
        "score":      0,
        "checks":     [],
        "issues":     [],
        "summary":    {},
        "error":      reason,
    }
