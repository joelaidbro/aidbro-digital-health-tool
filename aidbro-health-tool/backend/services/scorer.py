"""
Digital Health Score Calculator — v2
======================================
Total: 100 points across 5 pillars

Pillar 1 — Google Business Profile  : 30 pts
Pillar 2 — Website Quality          : 25 pts
Pillar 3 — Social Media Presence    : 20 pts  ← context-aware by category
Pillar 4 — Online Reputation        : 15 pts
Pillar 5 — Competitive Position     : 10 pts
"""

# ── Category → platform relevance weights ────────────────────────────────────
# Values: "high" (full points), "medium" (half points), "skip" (not evaluated)
CATEGORY_SOCIAL_WEIGHTS = {
    # Local Services
    "Retail / Shop":                  {"instagram": "high",   "facebook": "high",   "linkedin": "skip"},
    "Restaurant / Food & Beverage":   {"instagram": "high",   "facebook": "high",   "linkedin": "skip"},
    "Clinic / Healthcare":            {"instagram": "medium", "facebook": "high",   "linkedin": "medium"},
    "Salon & Beauty":                 {"instagram": "high",   "facebook": "high",   "linkedin": "skip"},
    "Gym & Fitness":                  {"instagram": "high",   "facebook": "high",   "linkedin": "skip"},
    "Hotel & Hospitality":            {"instagram": "high",   "facebook": "high",   "linkedin": "medium"},
    "Jewellery & Gold":               {"instagram": "high",   "facebook": "high",   "linkedin": "skip"},
    "Pharmacy":                       {"instagram": "medium", "facebook": "high",   "linkedin": "skip"},
    "Automobile / Garage":            {"instagram": "medium", "facebook": "high",   "linkedin": "skip"},
    "Supermarket / Grocery":          {"instagram": "medium", "facebook": "high",   "linkedin": "skip"},
    "Electronics Store":              {"instagram": "medium", "facebook": "high",   "linkedin": "skip"},
    "Furniture & Home Décor":         {"instagram": "high",   "facebook": "high",   "linkedin": "skip"},
    "Clothing & Apparel":             {"instagram": "high",   "facebook": "high",   "linkedin": "skip"},
    # Professional Services
    "IT / Software Company":          {"instagram": "medium", "facebook": "medium", "linkedin": "high"},
    "Education / Coaching Centre":    {"instagram": "medium", "facebook": "high",   "linkedin": "medium"},
    "Real Estate":                    {"instagram": "high",   "facebook": "high",   "linkedin": "medium"},
    "Legal / Advocate":               {"instagram": "skip",   "facebook": "medium", "linkedin": "high"},
    "Chartered Accountant / Finance": {"instagram": "skip",   "facebook": "medium", "linkedin": "high"},
    "Architect / Interior Design":    {"instagram": "high",   "facebook": "high",   "linkedin": "medium"},
    "Event Management":               {"instagram": "high",   "facebook": "high",   "linkedin": "medium"},
    "Photography / Studio":           {"instagram": "high",   "facebook": "high",   "linkedin": "skip"},
    "Advertising / Marketing Agency": {"instagram": "high",   "facebook": "high",   "linkedin": "high"},
    "Consulting / Business Services": {"instagram": "skip",   "facebook": "medium", "linkedin": "high"},
    # Industry & Trade
    "Manufacturing":                  {"instagram": "skip",   "facebook": "medium", "linkedin": "high"},
    "Construction":                   {"instagram": "medium", "facebook": "medium", "linkedin": "high"},
    "Textile / Garments":             {"instagram": "high",   "facebook": "high",   "linkedin": "medium"},
    "Agriculture / Farm":             {"instagram": "medium", "facebook": "high",   "linkedin": "skip"},
    "Export / Import":                {"instagram": "skip",   "facebook": "medium", "linkedin": "high"},
    "Logistics / Transport":          {"instagram": "skip",   "facebook": "medium", "linkedin": "high"},
    "Printing & Packaging":           {"instagram": "medium", "facebook": "medium", "linkedin": "medium"},
    "Wholesale / Distribution":       {"instagram": "skip",   "facebook": "medium", "linkedin": "medium"},
    # Other
    "E-commerce / Online Store":      {"instagram": "high",   "facebook": "high",   "linkedin": "skip"},
    "NGO / Trust / Charity":          {"instagram": "medium", "facebook": "high",   "linkedin": "medium"},
    "Government / PSU":               {"instagram": "skip",   "facebook": "medium", "linkedin": "medium"},
    "General Business":               {"instagram": "medium", "facebook": "high",   "linkedin": "medium"},
}

# Platform-specific messaging per relevance level
PLATFORM_MESSAGES = {
    "instagram": {
        "high": {
            "pass": "Instagram presence confirmed — great for visual marketing.",
            "fail": "No Instagram found. For your business type, Instagram is essential for customer reach.",
            "fix":  "Create an Instagram Business account and post product/service photos weekly.",
        },
        "medium": {
            "pass": "Instagram presence found — helpful for brand visibility.",
            "fail": "No Instagram found. Recommended but not critical for your business type.",
            "fix":  "Consider creating an Instagram account to showcase your work to a wider audience.",
        },
        "skip": {
            "pass": "",
            "fail": "",
            "fix":  "",
        },
    },
    "facebook": {
        "high": {
            "pass": "Facebook page detected — key channel for local customer trust.",
            "fail": "No Facebook page found. Facebook is critical for local discovery in India.",
            "fix":  "Create a Facebook Business Page immediately — it's free and drives local enquiries.",
        },
        "medium": {
            "pass": "Facebook page found — good for community presence.",
            "fail": "No Facebook page detected. Recommended for your business type.",
            "fix":  "A Facebook Business Page helps customers find and message you easily.",
        },
        "skip": {
            "pass": "",
            "fail": "",
            "fix":  "",
        },
    },
    "linkedin": {
        "high": {
            "pass": "LinkedIn presence confirmed — essential for B2B credibility.",
            "fail": "No LinkedIn found. For your business type, LinkedIn drives professional leads.",
            "fix":  "Create a LinkedIn Company Page to build B2B credibility and generate professional leads.",
        },
        "medium": {
            "pass": "LinkedIn presence found — adds professional credibility.",
            "fail": "No LinkedIn page found. Useful for building professional trust.",
            "fix":  "A LinkedIn Company Page helps you connect with business clients and partners.",
        },
        "skip": {
            "pass": "",
            "fail": "",
            "fix":  "",
        },
    },
}


def _get_social_weights(category: str) -> dict:
    """Return platform weights for a given business category."""
    return CATEGORY_SOCIAL_WEIGHTS.get(category, CATEGORY_SOCIAL_WEIGHTS["General Business"])


def _platform_points(weight: str, total_pool: int) -> int:
    """Convert a weight string to actual points from the pool."""
    if weight == "high":   return total_pool
    if weight == "medium": return total_pool // 2
    return 0  # skip


PILLAR_WEIGHTS = {
    "google_business": 20,
    "website": 50,
    "social_media": 10,
    "reputation": 10,
    "competitor": 10,
}


def calculate_score(
    google_data: dict,
    pagespeed_data: dict,
    social_data: dict,
    category: str = "General Business",
    seo_data: dict = None,
) -> dict:
    pillars = {}

    # ══════════════════════════════════════════════════════════════════════
    # PILLAR 1 — Google Business Profile (30 pts)
    # ══════════════════════════════════════════════════════════════════════
    p1 = []

    p1.append(_check("Profile found on Google", google_data.get("found", False), 5, 5,
        "Your business is listed on Google.",
        "Business not found on Google. Claim your profile immediately.",
        "Go to business.google.com and create/verify your profile.", "Digital Marketing"))

    rating = google_data.get("rating", 0)
    p1.append(_check("Star rating ≥ 4.0", rating >= 4.0, 5, 5,
        f"Good rating of {rating}/5 ★",
        f"Low rating of {rating}/5 ★ — actively losing customers.",
        "Respond to all reviews and ask happy customers to leave feedback.", "Digital Marketing",
        value=f"{rating} ★"))

    reviews = google_data.get("total_reviews", 0)
    rev_pts = 5 if reviews >= 20 else (3 if reviews >= 10 else (1 if reviews >= 5 else 0))
    p1.append({
        "check": "Review count", "passed": reviews >= 10,
        "points_earned": rev_pts, "points_max": 5,
        "value": f"{reviews} reviews",
        "message": f"{reviews} reviews." if reviews >= 10 else f"Only {reviews} reviews — too few for customer trust.",
        "fix": "Run a WhatsApp review request campaign to existing customers.", "service": "Digital Marketing",
    })

    photos = google_data.get("photos_count", 0)
    p1.append(_check("Photos uploaded (10+)", photos >= 10, 4, 4,
        f"{photos} photos attract more customers.",
        f"Only {photos} photos. Listings with 10+ photos get 42% more direction requests.",
        "Upload storefront, interior, product, and team photos.", "Digital Marketing",
        value=f"{photos} photos"))

    p1.append(_check("Business hours listed", google_data.get("has_hours", False), 3, 3,
        "Business hours visible to customers.",
        "No hours listed — customers don't know when you're open.",
        "Add accurate opening hours in your Google Business Profile.", "Digital Marketing"))

    p1.append(_check("Profile status operational", google_data.get("business_status") == "OPERATIONAL", 3, 3,
        "Google lists this business as operational.",
        "Google is not showing this profile as fully operational.",
        "Check your Google Business Profile status and complete verification if needed.", "Digital Marketing"))

    p1.append(_check("Website linked on Google", bool(google_data.get("website")), 3, 3,
        "Website linked — customers can visit your site from Google.",
        "No website linked — losing traffic to competitors.",
        "Link your website on Google Business Profile.", "Web Development"))

    p1.append(_check("Phone number listed", bool(google_data.get("phone")), 2, 2,
        "Phone number visible for direct calls.",
        "No phone number — customers cannot contact you directly.",
        "Add your active phone number to Google Business Profile.", "Digital Marketing"))

    p1_score = sum(c["points_earned"] for c in p1)
    pillars["google_business"] = _pillar("Google Business Profile", "🗺️", p1_score, 30, p1)

    # ══════════════════════════════════════════════════════════════════════
    # PILLAR 2 — Website Quality (25 pts)
    # ══════════════════════════════════════════════════════════════════════
    p2 = []
    has_web = pagespeed_data.get("found", False)

    p2.append(_check("Website exists", has_web, 7, 7,
        "You have a website — essential digital presence.",
        "No website found. 80% of customers search online before visiting.",
        "Get a professional business website built.", "Web Development"))

    if has_web:
        perf = pagespeed_data.get("performance_score", 0)
        p2.append({
            "check": "Mobile performance", "passed": perf >= 70,
            "points_earned": 5 if perf >= 70 else (3 if perf >= 50 else 1),
            "points_max": 5, "value": f"{perf}/100",
            "message": f"Mobile performance {perf}/100." + (" Good speed." if perf >= 70 else " Slow — users leave."),
            "fix": "Optimise images, enable caching, upgrade hosting.", "service": "Web Development",
        })

        seo = pagespeed_data.get("seo_score", 0)
        p2.append({
            "check": "SEO score", "passed": seo >= 70,
            "points_earned": 5 if seo >= 70 else (2 if seo >= 50 else 0),
            "points_max": 5, "value": f"{seo}/100",
            "message": f"SEO score {seo}/100." + (" Google reads your site well." if seo >= 70 else " Poor SEO — Google ignores you."),
            "fix": "Fix meta tags, add structured data, ensure mobile-friendliness.", "service": "Digital Marketing",
        })

        p2.append(_check("Fast page load (≤ 3s)", pagespeed_data.get("fast_load", False), 4, 4,
            f"Fast load: {pagespeed_data.get('lcp','N/A')}",
            f"Slow load: {pagespeed_data.get('lcp','N/A')} — users leave after 3s.",
            "Compress images, use CDN, reduce plugins.", "Web Development",
            value=pagespeed_data.get("lcp", "N/A")))

        p2.append(_check("Secure HTTPS", pagespeed_data.get("is_https", False), 2, 2,
            "HTTPS — secure and trusted by Google.",
            "HTTP only — browsers mark it insecure, Google penalises it.",
            "Install a free SSL certificate via Let's Encrypt.", "Web Development"))
    else:
        for name, pts in [("Mobile performance", 5), ("SEO score", 5), ("Fast page load", 4), ("Secure HTTPS", 2)]:
            p2.append({"check": name, "passed": False, "points_earned": 0, "points_max": pts,
                       "value": "N/A", "message": "Requires a website.", "fix": "Build a website first.", "service": "Web Development"})

    # ── Inject SEO crawler checks into Pillar 2 ───────────────────────────
    # These come from seo_crawler.py and add up to 13 additional points.
    # Pillar 2 max becomes 25 + 13 = 38, but we cap display at the earned total.
    seo_checks = (seo_data or {}).get("checks", [])
    if seo_checks:
        for sc in seo_checks:
            p2.append({
                "check":         sc.get("check", ""),
                "passed":        sc.get("passed", False),
                "points_earned": sc.get("points_earned", 0),
                "points_max":    sc.get("points_max", 0),
                "value":         sc.get("value", ""),
                "message":       sc.get("message", ""),
                "fix":           sc.get("fix", ""),
                "service":       sc.get("service", "Web Development"),
                "skipped":       False,
                "from_seo_crawler": True,  # tag for frontend display
            })

    p2_max   = sum(c["points_max"] for c in p2)
    p2_score = min(sum(c["points_earned"] for c in p2), p2_max)
    pillars["website"] = _pillar("Website Quality", "🌐", p2_score, p2_max, p2)

    # ══════════════════════════════════════════════════════════════════════
    # PILLAR 3 — Social Media Presence (20 pts) — CONTEXT-AWARE
    # ══════════════════════════════════════════════════════════════════════
    p3      = []
    weights = _get_social_weights(category)

    # Points pool: Instagram + Facebook + LinkedIn + WhatsApp = 20 total
    # WhatsApp always gets 5 pts regardless of category (universal in India)
    # The remaining 15 are distributed across Instagram, Facebook, LinkedIn
    # based on category weights.

    # Calculate how many "active" platforms there are (not skipped)
    active_platforms = [p for p in ["instagram", "facebook", "linkedin"] if weights.get(p) != "skip"]
    # Distribute remaining 15 pts across active platforms
    pts_per_platform = 15 // max(len(active_platforms), 1) if active_platforms else 5

    for platform in ["instagram", "facebook", "linkedin"]:
        weight = weights.get(platform, "medium")
        msgs   = PLATFORM_MESSAGES[platform][weight]

        if weight == "skip":
            # Not relevant — add a neutral note, 0 pts, not counted in max either
            p3.append({
                "check": f"{platform.capitalize()} presence",
                "passed": True,  # treated as N/A — doesn't penalise
                "points_earned": 0,
                "points_max": 0,
                "value": "Not required",
                "message": f"{platform.capitalize()} is not a key channel for your business type.",
                "fix": "",
                "service": "Social Media",
                "skipped": True,
            })
            continue

        found    = social_data.get(platform, False)
        max_pts  = pts_per_platform
        earned   = _platform_points(weight, max_pts) if found else 0

        # Adjust message if manually verified vs auto-detected
        manual   = platform in social_data.get("manual_verified", [])
        verified_note = " ✓ Manually verified." if manual else " (auto-detected)"

        p3.append({
            "check": f"{platform.capitalize()} presence",
            "passed": found,
            "points_earned": earned,
            "points_max": max_pts,
            "value": "Found" + (verified_note if found else ""),
            "message": (msgs["pass"] + verified_note) if found else msgs["fail"],
            "fix": msgs["fix"] if not found else "",
            "service": "Social Media Marketing",
            "skipped": False,
        })

    # WhatsApp Business — always evaluated (5 pts)
    wa = social_data.get("whatsapp_business", False)
    p3.append(_check("WhatsApp Business", wa, 5, 5,
        "WhatsApp Business detected — preferred channel for Kerala & Indian customers.",
        "No WhatsApp Business found. Most Indian customers prefer WhatsApp for enquiries.",
        "Set up WhatsApp Business with catalogue, auto-reply, and business hours.",
        "Digital Marketing"))

    # Recalculate max considering skipped platforms
    p3_max   = sum(c["points_max"] for c in p3)
    p3_score = min(sum(c["points_earned"] for c in p3), p3_max)

    # Store the actual max so the pillar card shows the right denominator
    pillars["social_media"] = _pillar(
        "Social Media Presence", "📱", p3_score, p3_max, p3,
        note=f"Scored out of {p3_max} pts (LinkedIn not required for {category})"
              if any(c.get("skipped") for c in p3) else ""
    )

    # ══════════════════════════════════════════════════════════════════════
    # PILLAR 4 — Online Reputation (15 pts)
    # ══════════════════════════════════════════════════════════════════════
    p4 = []

    rating = google_data.get("rating", 0)
    rep_pts = 5 if rating >= 4.5 else (4 if rating >= 4.0 else (2 if rating >= 3.5 else 0))
    p4.append({
        "check": "Overall star rating", "passed": rating >= 4.0,
        "points_earned": rep_pts, "points_max": 5, "value": f"{rating} ★",
        "message": (f"Excellent {rating}★ — strong social proof." if rating >= 4.5
                    else f"Good {rating}★." if rating >= 4.0
                    else f"Average {rating}★ — improve it." if rating >= 3.5
                    else f"Low {rating}★ — losing customers."),
        "fix": "Respond to all reviews. Resolve complaints. Request reviews from happy customers.",
        "service": "Digital Marketing",
    })

    reviews  = google_data.get("total_reviews", 0)
    rev_pts2 = 5 if reviews >= 50 else (4 if reviews >= 20 else (2 if reviews >= 10 else 0))
    p4.append({
        "check": "Review volume", "passed": reviews >= 20,
        "points_earned": rev_pts2, "points_max": 5, "value": f"{reviews} reviews",
        "message": (f"Strong review count ({reviews}) builds trust." if reviews >= 20
                    else f"Low count ({reviews}) — looks inactive to customers."),
        "fix": "Run a monthly WhatsApp review campaign to existing customers.",
        "service": "Digital Marketing",
    })

    competitors = google_data.get("nearby_competitors", [])
    if competitors:
        avg = sum(c.get("reviews", 0) for c in competitors) / len(competitors)
        better = reviews > avg
        p4.append({
            "check": "Reviews vs. local competitors", "passed": better,
            "points_earned": 5 if better else 0, "points_max": 5,
            "value": f"Avg competitor: {round(avg)}",
            "message": (f"More reviews than the local average ({round(avg)})." if better
                        else f"Competitors average {round(avg)} reviews vs your {reviews}."),
            "fix": "Focus on getting more Google reviews than your nearest competitors.",
            "service": "Digital Marketing",
        })
    else:
        p4.append({"check": "Reviews vs. local competitors", "passed": False,
                   "points_earned": 0, "points_max": 5, "value": "No data",
                   "message": "Competitor comparison needs Google API.", "fix": "", "service": "Digital Marketing"})

    p4_score = sum(c["points_earned"] for c in p4)
    pillars["reputation"] = _pillar("Online Reputation", "⭐", p4_score, 15, p4)

    # ══════════════════════════════════════════════════════════════════════
    # PILLAR 5 — Competitive Position (10 pts)
    # ══════════════════════════════════════════════════════════════════════
    p5 = []

    checked = [pillars["google_business"], pillars["website"],
               pillars["social_media"], pillars["reputation"]]
    total_passed = sum(1 for p in checked for c in p["checks"] if c.get("passed") and not c.get("skipped"))
    total_checks = sum(1 for p in checked for c in p["checks"] if not c.get("skipped"))
    pass_rate    = total_passed / total_checks if total_checks else 0

    comp_pts = 10 if pass_rate >= 0.7 else (6 if pass_rate >= 0.5 else (3 if pass_rate >= 0.3 else 0))
    p5.append({
        "check": "Overall digital completeness vs local average",
        "passed": pass_rate >= 0.6,
        "points_earned": comp_pts, "points_max": 10,
        "value": f"{round(pass_rate * 100)}% complete",
        "message": ("Digital presence stronger than local average." if pass_rate >= 0.6
                    else "Digital profile weaker than most local competitors."),
        "fix": "Fix the highest-priority issues above to leap ahead of local competition.",
        "service": "All Aidbro Services",
    })

    p5_score = sum(c["points_earned"] for c in p5)
    pillars["competitor"] = _pillar("Competitive Position", "🏆", p5_score, 10, p5)

    # ── Total ─────────────────────────────────────────────────────────────────
    total = min(
        round(
            sum(
                ((pillar["score"] / pillar["max"]) * PILLAR_WEIGHTS.get(key, 0))
                if pillar["max"] else 0
                for key, pillar in pillars.items()
            )
        ),
        100,
    )
    grade = "A" if total >= 80 else "B" if total >= 65 else "C" if total >= 50 else "D" if total >= 35 else "F"
    label = {"A": "Excellent", "B": "Good", "C": "Average", "D": "Needs Work", "F": "Critical"}[grade]

    # Top 3 unfixed items sorted by max points
    all_failed = [
        {"check": c["check"], "fix": c.get("fix",""), "service": c.get("service",""), "impact": c["points_max"]}
        for p in pillars.values() for c in p["checks"]
        if not c.get("passed") and not c.get("skipped") and c.get("fix")
    ]
    all_failed.sort(key=lambda x: x["impact"], reverse=True)

    return {
        "total_score": total,
        "grade":       grade,
        "label":       label,
        "category":    category,
        "weighting":   PILLAR_WEIGHTS,
        "pillars":     pillars,
        "top_fixes":   all_failed[:3],
        "is_mocked":   google_data.get("mocked", False),
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _check(name, condition, pts_pass, pts_max, pass_msg, fail_msg, fix, service, value=""):
    return {
        "check":         name,
        "passed":        condition,
        "points_earned": pts_pass if condition else 0,
        "points_max":    pts_max,
        "value":         value,
        "message":       pass_msg if condition else fail_msg,
        "fix":           fix,
        "service":       service,
        "skipped":       False,
    }


def _pillar(name, icon, score, max_score, checks, note=""):
    pct   = round((score / max_score) * 100) if max_score else 0
    color = "green" if pct >= 75 else "yellow" if pct >= 50 else "red"
    return {
        "name":    name,
        "icon":    icon,
        "score":   score,
        "max":     max_score,
        "percent": pct,
        "checks":  checks,
        "color":   color,
        "note":    note,
    }
