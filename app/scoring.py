"""Source credibility tiers and the rule-based verdict.

Everything here is deterministic and unit-tested, so every verdict can be explained.
"""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from .claims import tokens
from .sources import (
    CONFIRM_TERMS, DEBUNK_TERMS, FACTCHECK_DOMAINS, FACTCHECK_NAMES, FACTCHECK_PATH_HINTS,
    GOV_DOMAINS, GOV_NAMES, GOV_SUFFIXES, NEWS_DOMAINS, NEWS_NAMES,
)

YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")
REDIRECT_DOMAINS = {"news.google.com", "google.com"}

VERDICT_LABELS = {
    "likely_false": "Likely false",
    "misleading": "Misleading",
    "unverified": "Unverified",
    "supported": "Supported",
}


# -- source classification ------------------------------------------------
def domain_of(link: str) -> str:
    if not link:
        return ""
    parsed = urlparse(link if "//" in link else "//" + link)
    host = parsed.netloc.lower().split("@")[-1].split(":")[0]
    return host[4:] if host.startswith("www.") else host


def _match(domain: str, domains: set[str]) -> bool:
    return any(domain == d or domain.endswith("." + d) for d in domains)


def tier_of(domain: str, link: str = "", source_name: str = "") -> str:
    """Return one of: factcheck, gov, news, other."""
    if domain in REDIRECT_DOMAINS or not domain:
        name = (source_name or "").lower()
        if any(n in name for n in FACTCHECK_NAMES):
            return "factcheck"
        if any(n in name for n in GOV_NAMES):
            return "gov"
        if any(n in name for n in NEWS_NAMES):
            return "news"
        return "other"
    if _match(domain, FACTCHECK_DOMAINS):
        return "factcheck"
    if domain.endswith(GOV_SUFFIXES) or _match(domain, GOV_DOMAINS):
        return "gov"
    if _match(domain, NEWS_DOMAINS):
        path = link.lower()
        return "factcheck" if any(h in path for h in FACTCHECK_PATH_HINTS) else "news"
    return "other"


def has_term(text: str, terms: tuple[str, ...]) -> bool:
    low = (text or "").lower()
    return any(t in low for t in terms)


def overlap(claim_tokens: set[str], text: str) -> float:
    """Share of the claim's key words that appear in a result (0..1)."""
    if not claim_tokens:
        return 0.0
    hits = len(claim_tokens & set(tokens(text)))
    return min(1.0, hits / min(len(claim_tokens), 6))


def classify_item(item: dict[str, Any], claim_tokens: set[str] | None = None) -> dict[str, Any]:
    link = item.get("link", "") or ""
    source = item.get("source", "") or ""
    domain = domain_of(link)
    tier = tier_of(domain, link, source)
    text = f"{item.get('title', '')} {item.get('snippet', '')}"
    item["domain"] = (source.lower() if domain in REDIRECT_DOMAINS or not domain else domain) or link
    item["tier"] = tier
    item["debunk_hit"] = has_term(text, DEBUNK_TERMS)
    item["confirm_hit"] = has_term(text, CONFIRM_TERMS)
    if claim_tokens is not None:
        item["overlap"] = round(overlap(claim_tokens, text), 2)
    return item


# -- weights ---------------------------------------------------------------
def _debunk_weight(it: dict[str, Any]) -> float:
    ov, tier, hit = it.get("overlap", 0.0), it["tier"], it["debunk_hit"]
    if tier == "factcheck" and ov >= 0.25:
        return 3.0 if hit else (0.0 if it["confirm_hit"] else 1.0)
    if tier in ("gov", "news") and hit and ov >= 0.25:
        return 2.0
    if hit and ov >= 0.4:
        return 0.5
    return 0.0


def _support_weight(it: dict[str, Any]) -> float:
    ov, tier = it.get("overlap", 0.0), it["tier"]
    if it["debunk_hit"]:
        return 0.0
    if tier == "factcheck" and it["confirm_hit"] and ov >= 0.25:
        return 2.0
    if tier == "gov" and ov >= 0.4:
        return 2.0
    if tier == "news" and ov >= 0.4:
        return 1.5
    return 0.0


def _stance(it: dict[str, Any], wd: float, ws: float) -> str:
    if wd > 0 and wd >= ws:
        if wd >= 2:
            return "refutes"
        return "fact-checked" if it["tier"] == "factcheck" else "related"
    if ws > 0:
        return "supports"
    return "context"


# -- image provenance -----------------------------------------------------------
def analyse_image(matches: list[dict[str, Any]], current_year: int) -> dict[str, Any]:
    for m in matches:
        classify_item(m)
    flagged = [m for m in matches if m["tier"] == "factcheck" or m["debunk_hit"]]
    years = sorted(
        {
            int(y)
            for m in matches
            for y in YEAR_RE.findall(f"{m.get('title', '')} {m.get('snippet', '')}")
            if int(y) <= current_year
        }
    )
    earliest = years[0] if years else None
    older = earliest is not None and earliest < current_year
    score = (2.0 if flagged else 0.0) + (1.0 if older else 0.0)
    notes = []
    if flagged:
        notes.append(f"The image appears on {len(flagged)} page(s) from fact-checkers or with debunking language.")
    if older:
        notes.append(
            f"Pages matching this image mention {earliest}, earlier than {current_year}: it may be recycled."
        )
    return {
        "matches": matches,
        "flagged": len(flagged),
        "earliest_year": earliest,
        "possibly_recycled": bool(older),
        "score": min(score, 3.0),
        "notes": notes,
    }


# -- verdict ------------------------------------------------------------------------
def _label(conf: int) -> str:
    return "High" if conf >= 75 else "Medium" if conf >= 55 else "Low"


def assess(items: list[dict[str, Any]], image: dict[str, Any] | None = None) -> dict[str, Any]:
    """items must already be passed through classify_item(item, claim_tokens)."""
    deb: dict[str, tuple[float, dict[str, Any]]] = {}
    sup: dict[str, tuple[float, dict[str, Any]]] = {}
    for it in items:
        key = it["domain"] or it.get("link", "")
        wd, ws = _debunk_weight(it), _support_weight(it)
        it["stance"] = _stance(it, wd, ws)
        if wd > deb.get(key, (0.0, None))[0]:
            deb[key] = (wd, it)
        if ws > sup.get(key, (0.0, None))[0]:
            sup[key] = (ws, it)

    image_score = image["score"] if image else 0.0
    debunk = sum(w for w, _ in deb.values())
    support = sum(w for w, _ in sup.values())
    debunk_total = debunk + image_score

    split = debunk_total >= 1.5 and support >= 1.5 and abs(debunk_total - support) < 1.5
    if split:
        verdict = "unverified"
    elif debunk_total >= 3:
        verdict = "likely_false"
    elif debunk_total >= 1.5:
        verdict = "misleading"
    elif support >= 3:
        verdict = "supported"
    else:
        verdict = "unverified"

    if verdict == "likely_false":
        confidence = min(95, int(55 + 8 * debunk_total))
    elif verdict == "misleading":
        confidence = min(80, int(45 + 10 * debunk_total))
    elif verdict == "supported":
        confidence = min(90, int(40 + 12 * support))
    else:
        confidence = 30 if not (debunk_total or support) else 40

    fact_checkers = [it for w, it in deb.values() if it["tier"] == "factcheck" and w >= 1]
    outlets_debunking = [it for w, it in deb.values() if it["tier"] in ("gov", "news") and w >= 2]
    corroborating = [it for _, it in sup.values()]

    reasons: list[str] = []
    if fact_checkers:
        names = ", ".join(sorted({it["domain"] for it in fact_checkers})[:3])
        reasons.append(f"{len(fact_checkers)} fact-checking source(s) covered this claim ({names}).")
    if outlets_debunking:
        reasons.append(f"{len(outlets_debunking)} news or official source(s) use debunking language about it.")
    if image:
        reasons.extend(image["notes"])
    if corroborating:
        reasons.append(f"{len(corroborating)} credible or official source(s) report the same thing without debunking it.")
    if split:
        reasons.append("Credible sources disagree, so no firm verdict. Both sides are listed below.")
    if not reasons:
        reasons.append(
            "No credible outlet or fact-checker has clearly covered this yet. "
            "Missing coverage is not proof either way."
        )
    if verdict == "unverified":
        reasons.append("Hold off forwarding until an official or well-known source confirms it.")

    def ranked(pool: dict[str, tuple[float, dict[str, Any]]]) -> list[dict[str, Any]]:
        return [it for _w, it in sorted(pool.values(), key=lambda p: -p[0])][:4]

    refuting = [it for w, it in sorted(deb.values(), key=lambda p: -p[0]) if w >= 1][:4]
    supporting = ranked(sup)
    return {
        "verdict": verdict,
        "label": VERDICT_LABELS[verdict],
        "confidence": confidence,
        "confidence_label": _label(confidence),
        "debunk_score": round(debunk_total, 1),
        "support_score": round(support, 1),
        "conflict": split or (debunk_total >= 1.5 and support >= 1.5),
        "reasons": reasons,
        "refuting": refuting,
        "supporting": supporting,
    }


# -- shareable reply ---------------------------------------------------------------------
_EN = {
    "likely_false": "Hi 🙏 I checked this message and it looks false. Please don't forward it. What the sources say:",
    "misleading": "Hi 🙏 I checked this: it's misleading (old, recycled or missing context). Details:",
    "supported": "I checked this and credible sources confirm it. Sources:",
    "unverified": "I couldn't find reliable confirmation for this yet, so let's not forward it until an official source confirms it.",
}
_HI = {
    "likely_false": "नमस्ते 🙏 मैंने इस मैसेज की जांच की, यह गलत लग रहा है। कृपया इसे आगे न भेजें। स्रोत:",
    "misleading": "नमस्ते 🙏 मैंने जांच की, यह मैसेज भ्रामक है (पुराना या संदर्भ से हटकर)। विवरण:",
    "supported": "मैंने जांच की, भरोसेमंद स्रोत इसकी पुष्टि करते हैं। स्रोत:",
    "unverified": "मुझे इसकी पुष्टि करने वाला भरोसेमंद स्रोत अभी नहीं मिला। किसी आधिकारिक स्रोत से पुष्टि होने तक इसे आगे न भेजें।",
}


def build_reply(verdict: str, language: str, assessment: dict[str, Any]) -> str:
    templates = _HI if language == "hi" else _EN
    lines = [templates[verdict]]
    pool = assessment["supporting"] if verdict == "supported" else assessment["refuting"]
    for it in pool[:3]:
        lines.append(f"• {it.get('source') or it['domain']}: {it['link']}")
    return "\n".join(lines)
