"""
analyzer.py
Rule-based scoring (always runs) + optional Claude API feedback layer
that falls back gracefully if no API key is set or the call fails.
"""
import os
import re
import json
from collections import Counter

ACTION_VERBS = {
    "achieved", "administered", "analyzed", "architected", "automated", "built",
    "championed", "collaborated", "created", "delivered", "deployed", "designed",
    "developed", "directed", "drove", "engineered", "established", "executed",
    "generated", "implemented", "improved", "increased", "initiated", "launched",
    "led", "managed", "mentored", "migrated", "negotiated", "optimized",
    "orchestrated", "overhauled", "pioneered", "presented", "produced",
    "reduced", "refactored", "resolved", "restructured", "scaled", "shipped",
    "simplified", "spearheaded", "streamlined", "strengthened", "transformed",
}

WEAK_PHRASES = [
    "responsible for", "worked on", "helped with", "duties included",
    "in charge of", "tasked with", "was involved in",
]

SECTION_KEYWORDS = {
    "summary": ["summary", "objective", "profile"],
    "experience": ["experience", "employment", "work history"],
    "education": ["education", "academic"],
    "skills": ["skills", "technologies", "technical skills", "competencies"],
    "projects": ["projects", "portfolio"],
}

STOPWORDS = {
    "the", "and", "for", "with", "you", "your", "our", "will", "are", "this",
    "that", "have", "from", "must", "able", "who", "role", "job", "work",
    "team", "into", "such", "than", "then", "they", "them", "their", "not",
    "can", "all", "any", "may", "including", "using", "use",
    "years", "year", "strong", "ability", "etc", "per", "within", "across",
    "looking", "seeking", "required", "requirements", "responsibilities",
    "preferred", "candidate", "candidates", "skills", "experience",
    "communication", "environment", "opportunity", "company", "position",
}

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(\+?\d{1,3}[\s.-]?)?\(?\d{3,4}\)?[\s.-]?\d{3}[\s.-]?\d{3,4}")
LINK_RE = re.compile(r"(linkedin\.com|github\.com)/\S+", re.IGNORECASE)


def _score_contact_info(text: str) -> dict:
    has_email = bool(EMAIL_RE.search(text))
    has_phone = bool(PHONE_RE.search(text))
    has_link = bool(LINK_RE.search(text))
    found = sum([has_email, has_phone, has_link])
    score = round((found / 3) * 100)
    missing = []
    if not has_email:
        missing.append("email address")
    if not has_phone:
        missing.append("phone number")
    if not has_link:
        missing.append("LinkedIn or GitHub link")
    return {"score": score, "missing": missing}


def _score_sections(text_lower: str) -> dict:
    found_sections = []
    missing_sections = []
    for section, keywords in SECTION_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            found_sections.append(section)
        else:
            missing_sections.append(section)
    score = round((len(found_sections) / len(SECTION_KEYWORDS)) * 100)
    return {"score": score, "found": found_sections, "missing": missing_sections}


def _score_action_verbs(text_lower: str) -> dict:
    words = re.findall(r"[a-z]+", text_lower)
    verb_hits = sum(1 for w in words if w in ACTION_VERBS)
    weak_hits = sum(text_lower.count(p) for p in WEAK_PHRASES)
    word_count = max(len(words), 1)
    density = verb_hits / word_count * 100
    score = min(round(density * 12), 100)
    penalty = min(weak_hits * 8, 40)
    score = max(score - penalty, 0)
    return {"score": score, "action_verb_count": verb_hits, "weak_phrase_count": weak_hits}


def _score_quantifiable(text: str) -> dict:
    lines = [l for l in text.split("\n") if l.strip()]
    bullet_like = [l for l in lines if len(l.strip()) > 15]
    quantified = sum(1 for line in bullet_like if re.search(r"\d", line))
    ratio = quantified / max(len(bullet_like), 1)
    score = round(ratio * 100)
    return {"score": score, "quantified_lines": quantified, "total_lines": len(bullet_like)}


def _score_length(text: str) -> dict:
    word_count = len(re.findall(r"\w+", text))
    if word_count < 150:
        score, note = 40, "Resume looks too short - add more detail on impact and scope."
    elif 150 <= word_count <= 250:
        score, note = 75, "A bit brief - there's room to add more accomplishments."
    elif 250 < word_count <= 900:
        score, note = 100, "Good length for a focused one-to-two-page resume."
    elif 900 < word_count <= 1200:
        score, note = 70, "Getting long - consider trimming to the most relevant experience."
    else:
        score, note = 45, "Resume is quite long - tighten it up to keep reviewers engaged."
    return {"score": score, "word_count": word_count, "note": note}


def _score_keyword_match(resume_text_lower: str, jd_text: str) -> dict:
    jd_words = re.findall(r"[a-zA-Z][a-zA-Z+#]{2,}", jd_text.lower())
    jd_keywords = [w for w in jd_words if w not in STOPWORDS]
    freq = Counter(jd_keywords)
    top_keywords = [w for w, _ in freq.most_common(25)]

    matched = [kw for kw in top_keywords if kw in resume_text_lower]
    missing = [kw for kw in top_keywords if kw not in resume_text_lower]

    score = round((len(matched) / len(top_keywords)) * 100) if top_keywords else 0
    return {"score": score, "matched": matched[:15], "missing": missing[:15]}


def rule_based_analysis(text: str, job_description: str | None = None) -> dict:
    text_lower = text.lower()

    contact = _score_contact_info(text)
    sections = _score_sections(text_lower)
    verbs = _score_action_verbs(text_lower)
    quant = _score_quantifiable(text)
    length = _score_length(text)

    components = {
        "contact_info": contact["score"],
        "sections": sections["score"],
        "action_verbs": verbs["score"],
        "quantifiable_impact": quant["score"],
        "length": length["score"],
    }
    weights = {
        "contact_info": 0.10, "sections": 0.20, "action_verbs": 0.25,
        "quantifiable_impact": 0.25, "length": 0.20,
    }

    keyword_match = None
    if job_description and job_description.strip():
        keyword_match = _score_keyword_match(text_lower, job_description)
        components["keyword_match"] = keyword_match["score"]
        weights = {
            "contact_info": 0.08, "sections": 0.15, "action_verbs": 0.18,
            "quantifiable_impact": 0.19, "length": 0.15, "keyword_match": 0.25,
        }

    overall = round(sum(components[k] * weights[k] for k in components))

    return {
        "overall_score": overall,
        "components": components,
        "details": {
            "contact_info": contact, "sections": sections, "action_verbs": verbs,
            "quantifiable_impact": quant, "length": length, "keyword_match": keyword_match,
        },
    }


def _build_fallback_feedback(rule_result: dict) -> dict:
    d = rule_result["details"]
    strengths, improvements, suggestions = [], [], []

    if d["contact_info"]["score"] >= 90:
        strengths.append("Contact details are complete and easy to find.")
    else:
        improvements.append("Contact info is incomplete: missing " + ", ".join(d["contact_info"]["missing"]) + ".")
        suggestions.append("Add a professional email, phone number, and LinkedIn/GitHub link near the top of your resume.")

    if d["sections"]["score"] >= 80:
        strengths.append("Resume covers the core sections recruiters expect.")
    else:
        improvements.append("Missing key sections: " + ", ".join(d["sections"]["missing"]) + ".")
        suggestions.append("Add clearly labeled sections for " + ", ".join(d["sections"]["missing"]) + ".")

    if d["action_verbs"]["score"] >= 70:
        strengths.append("Bullet points lead with strong action verbs.")
    else:
        improvements.append("Too many weak or passive phrases (e.g. 'responsible for').")
        suggestions.append("Rewrite bullets to start with strong verbs like 'led', 'built', 'optimized', or 'reduced'.")

    if d["quantifiable_impact"]["score"] >= 60:
        strengths.append("Good use of numbers to show measurable impact.")
    else:
        improvements.append("Most bullet points lack measurable results.")
        suggestions.append("Add numbers wherever possible: %, $, time saved, users impacted, team size.")

    if d["length"]["score"] < 100:
        improvements.append(d["length"]["note"])
    else:
        strengths.append(d["length"]["note"])

    if d["keyword_match"]:
        km = d["keyword_match"]
        if km["score"] < 60:
            suggestions.append("Weave in more of these role-specific keywords: " + ", ".join(km["missing"][:8]) + ".")
        else:
            strengths.append("Strong keyword overlap with the target job description.")

    summary = (
        f"Your resume scores {rule_result['overall_score']}/100 based on structure, "
        "clarity, and measurable impact. Focus first on the improvements listed below."
    )

    return {
        "summary": summary, "strengths": strengths, "improvements": improvements,
        "suggestions": suggestions, "rewritten_bullets": [], "source": "rule_based",
    }


def ai_enhance(resume_text: str, job_description: str | None, rule_result: dict) -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _build_fallback_feedback(rule_result)

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        jd_block = f"\n\nTARGET JOB DESCRIPTION:\n{job_description.strip()}" if job_description else ""

        prompt = f"""You are an expert resume reviewer and career coach. Analyze this resume and respond with ONLY a valid JSON object (no markdown fences, no preamble) with exactly these keys:
- "summary": one encouraging but honest paragraph (2-3 sentences) on overall quality
- "strengths": array of 3-5 short specific strength statements
- "improvements": array of 3-5 short specific weaknesses
- "suggestions": array of 3-5 concrete, actionable rewrite suggestions
- "rewritten_bullets": array of up to 3 objects, each with "original" and "improved" keys, rewriting the weakest bullet points from the resume to be stronger and more quantified

RESUME TEXT:
{resume_text[:6000]}
{jd_block}
"""

        response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )

        raw_text = "".join(
            block.text for block in response.content if getattr(block, "type", "") == "text"
        )
        cleaned = raw_text.strip().strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()

        parsed = json.loads(cleaned)
        parsed["source"] = "ai"
        parsed.setdefault("rewritten_bullets", [])
        return parsed

    except Exception:
        return _build_fallback_feedback(rule_result)