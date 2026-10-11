"""Turn a forwarded message into checkable claims and search queries.

Uses Claude when ANTHROPIC_API_KEY is set; otherwise falls back to a rule-based extractor so
the app works with only a SerpApi key.
"""
from __future__ import annotations

import json
import re
from typing import Any

import requests

from .config import Settings

DEVANAGARI = re.compile(r"[ऀ-ॿ]")
URL_RE = re.compile(r"https?://\S+|www\.\S+")
TOKEN_RE = re.compile(r"[\wऀ-ॿ]+", re.UNICODE)
SENT_SPLIT = re.compile(r"(?<=[.!?।])\s+|\n+")

STOPWORDS = set(
    """the and for that this with from have has are was were will would you your not but all can any
    our out who what when where which their there they them his her its into about over just than
    then also been being more most some such only very per via please kindly dear friends sir madam
    hai hain ho ka ki ke ko se me mein par aur ya yeh ye woh wo kya nahi nhi bhi hi to tha thi
    है हैं का की के को से में पर और या यह ये वह था थी थे भी ही तो एक जो कि कृपया""".split()
)

TRIGGERS = set(
    """government govt ban banned block blocked free alert warning urgent breaking
    virus cure scheme lakh crore police court tax mandatory expire expires suspend suspended
    arrest recall poison shocking exposed leaked
    सरकार फ्री बंद अलर्ट""".split()
)

# Calls to action ("share this with everyone") are not claims; short sentences made of them are skipped.
CTA_WORDS = set("share forward send spread tell आगे शेयर फॉरवर्ड भेजें".split())


def detect_language(text: str) -> str:
    return "hi" if DEVANAGARI.search(text or "") else "en"


def tokens(text: str, min_len: int = 3) -> list[str]:
    out: list[str] = []
    for tok in TOKEN_RE.findall((text or "").lower()):
        if tok in STOPWORDS:
            continue
        if tok.isdigit():
            out.append(tok)
            continue
        if len(tok) >= (2 if DEVANAGARI.search(tok) else min_len):
            out.append(tok)
    return out


def make_query(sentence: str, max_words: int = 9) -> str:
    seen: set[str] = set()
    words: list[str] = []
    for tok in tokens(URL_RE.sub(" ", sentence)):
        if tok not in seen:
            seen.add(tok)
            words.append(tok)
    return " ".join(words[:max_words])


def heuristic_claims(text: str, max_claims: int = 2) -> list[dict[str, str]]:
    clean = URL_RE.sub(" ", text or "").strip()
    sentences = [s.strip() for s in SENT_SPLIT.split(clean) if s and len(s.strip()) >= 20]
    if not sentences and clean:
        sentences = [clean[:200]]

    scored = []
    for idx, sent in enumerate(sentences):
        toks = TOKEN_RE.findall(sent.lower())
        score = (
            2.0 * any(ch.isdigit() for ch in sent)
            + 0.5 * sum(1 for w in sent.split()[1:] if w[:1].isupper())
            + 2.0 * sum(1 for t in toks if t in TRIGGERS)
            + min(len(sent) / 80, 1.0)
            - idx * 0.01
            - (3.0 if len(toks) <= 8 and any(t in CTA_WORDS for t in toks) else 0.0)
        )
        scored.append((score, idx, sent))

    ranked = sorted(scored, key=lambda x: (-x[0], x[1]))
    # Best claim always; extra claims only if they look like real claims (numbers or trigger words),
    # so greetings and sign-offs never cost a search credit.
    top = [ranked[0]] + [r for r in ranked[1:max_claims] if r[0] >= 1.0] if ranked else []
    claims = [{"claim": sent, "query": make_query(sent)} for _, _, sent in top]
    return [c for c in claims if c["query"]]


_LLM_SYSTEM = (
    "You extract checkable factual claims from viral messages written in English, Hindi or Hinglish. "
    "Return ONLY JSON: {\"claims\":[{\"claim\":\"<one sentence>\",\"search_query\":\"<=9 neutral words, "
    "no the words 'fact check'>\"}],\"topic\":\"<2-4 word topic for a trends lookup>\"}. "
    "At most 2 claims. Ignore greetings, emojis and calls to action like 'forward this'."
)


def llm_claims(text: str, settings: Settings) -> tuple[list[dict[str, str]], str] | None:
    """Ask Claude to extract claims. Returns None on any failure so the caller can fall back."""
    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": settings.anthropic_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": settings.llm_model,
                "max_tokens": 400,
                "system": _LLM_SYSTEM,
                "messages": [{"role": "user", "content": text}],
            },
            timeout=20,
        )
        resp.raise_for_status()
        raw = resp.json()["content"][0]["text"].strip()
        raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.MULTILINE).strip()
        data: dict[str, Any] = json.loads(raw)
        claims = [
            {"claim": str(c["claim"]), "query": str(c["search_query"]).strip()}
            for c in data.get("claims", [])[:2]
            if c.get("claim") and c.get("search_query")
        ]
        if not claims:
            return None
        return claims, str(data.get("topic", "")).strip()
    except Exception:  # noqa: BLE001 - any failure means "use the heuristic instead"
        return None


def extract_claims(text: str, settings: Settings) -> dict[str, Any]:
    language = detect_language(text)
    claims: list[dict[str, str]] = []
    topic = ""
    method = "heuristic"

    if settings.has_llm and text.strip():
        result = llm_claims(text, settings)
        if result:
            claims, topic = result
            method = "llm"
    if not claims:
        claims = heuristic_claims(text)
    if not topic and claims:
        topic = " ".join(claims[0]["query"].split()[:3])

    return {"claims": claims, "language": language, "method": method, "trend_keyword": topic}
