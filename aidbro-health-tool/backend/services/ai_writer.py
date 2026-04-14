import os
from groq import Groq

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")


def generate_insights(
    business_name: str,
    location: str,
    score_data: dict,
    google_data: dict,
) -> dict:
    """
    Use Groq (Llama 3.3) to generate a personalized summary, 
    key insight paragraph, and CTA message for the report.
    Returns: { summary, insight, cta, greeting }
    """
    if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_key_here":
        return _fallback_insights(business_name, score_data)

    try:
        client = Groq(api_key=GROQ_API_KEY)

        total = score_data.get("total_score", 0)
        grade = score_data.get("grade", "C")
        label = score_data.get("label", "Average")
        top_fixes = score_data.get("top_fixes", [])
        pillars = score_data.get("pillars", {})

        # Build a concise context string for the AI
        pillar_summary = "\n".join([
            f"- {p['name']}: {p['score']}/{p['max']} ({p['percent']}%)"
            for p in pillars.values()
        ])

        fix_summary = "\n".join([
            f"- {f['check']}: {f['fix']}"
            for f in top_fixes[:3]
        ])

        prompt = f"""You are a friendly digital marketing consultant for Aidbro, 
a company based in Kannur, Kerala. Write a personalized digital health report 
summary for the following business.

Business: {business_name}
Location: {location}
Digital Health Score: {total}/100 (Grade: {grade} — {label})

Pillar Scores:
{pillar_summary}

Top 3 Priority Fixes:
{fix_summary}

Write the following in a warm, honest, slightly urgent tone. 
Keep language simple — this is for a local business owner in Kerala.
Do NOT use markdown. Use plain text only.

1. GREETING (1 sentence, friendly, mention the business name)
2. SUMMARY (2 sentences — what does this score mean for their business?)
3. INSIGHT (2-3 sentences — what is their biggest risk if they don't fix these issues?)
4. CTA (1 sentence — encourage them to book a free consultation with Aidbro)

Format your response EXACTLY as:
GREETING: [text]
SUMMARY: [text]
INSIGHT: [text]
CTA: [text]"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.7,
        )

        raw = response.choices[0].message.content.strip()

        # Parse the structured response
        result = {}
        for key in ["GREETING", "SUMMARY", "INSIGHT", "CTA"]:
            for line in raw.split("\n"):
                if line.startswith(f"{key}:"):
                    result[key.lower()] = line.replace(f"{key}:", "").strip()
                    break

        # Fallback if parsing fails
        if len(result) < 4:
            return _fallback_insights(business_name, score_data)

        return result

    except Exception as e:
        print(f"[AI Writer] Groq error: {e}")
        return _fallback_insights(business_name, score_data)


def _fallback_insights(business_name: str, score_data: dict) -> dict:
    """Hardcoded fallback if Groq is unavailable."""
    total = score_data.get("total_score", 0)
    label = score_data.get("label", "Average")

    if total >= 70:
        summary = (
            f"{business_name} has a solid digital presence with a score of {total}/100. "
            "A few targeted improvements could make you the top choice in your area."
        )
        insight = (
            "Your competitors are actively improving their online presence. "
            "Staying ahead means acting on the gaps identified above before they do."
        )
    elif total >= 50:
        summary = (
            f"{business_name} scores {total}/100 — showing some digital presence "
            "but with clear gaps that are costing you customers daily."
        )
        insight = (
            "Customers searching online for your services are finding your competitors instead. "
            "Every day without fixing these issues is revenue walking out the door."
        )
    else:
        summary = (
            f"With a score of only {total}/100, {business_name} has critical gaps "
            "in its digital presence that are actively losing customers."
        )
        insight = (
            "In 2025, 85% of customers search online before visiting a local business. "
            "Your current digital presence means most of them will never find you."
        )

    return {
        "greeting": f"Hello! Here is your Digital Health Report for {business_name}.",
        "summary": summary,
        "insight": insight,
        "cta": (
            "Book a free 15-minute consultation with Aidbro and let us help you "
            "turn these gaps into growth — no cost, no commitment."
        )
    }