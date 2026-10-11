"""The ForwardCheck pipeline: claims -> SerpApi evidence -> scoring -> shareable reply."""
from __future__ import annotations

import time
from datetime import date
from typing import Any

from .claims import extract_claims, tokens
from .config import Settings
from .scoring import analyse_image, assess, build_reply, classify_item, has_term
from .serp import SerpError
from .sources import DEBUNK_TERMS

HEADLINES = {
    "likely_false": "Most of the evidence says this message is false.",
    "misleading": "This message looks misleading or recycled.",
    "supported": "Credible sources back this up.",
    "unverified": "Not enough credible evidence either way.",
}


# -- normalisers: SerpApi JSON -> small uniform dicts ---------------------------
def _name(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("name", ""))
    return str(value or "")


def norm_web(data: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "title": r.get("title", ""),
            "link": r.get("link", ""),
            "snippet": r.get("snippet", ""),
            "date": r.get("date", ""),
            "source": _name(r.get("source")) or r.get("displayed_link", ""),
            "engine": "google",
        }
        for r in (data.get("organic_results") or [])
        if r.get("link")
    ]


def _news_item(n: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": n.get("title", ""),
        "link": n.get("link", ""),
        "snippet": n.get("snippet", ""),
        "date": n.get("date", ""),
        "source": _name(n.get("source")),
        "engine": "google_news",
    }


def norm_news(data: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for n in data.get("news_results") or []:
        if n.get("stories"):
            out.extend(_news_item(s) for s in n["stories"])
        else:
            out.append(_news_item(n))
    return [i for i in out if i["link"]]


def norm_videos(data: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "title": v.get("title", ""),
            "link": v.get("link", ""),
            "channel": _name(v.get("channel")),
            "published": v.get("published_date", ""),
            "views": v.get("views", ""),
            "snippet": "",
            "source": _name(v.get("channel")),
        }
        for v in (data.get("video_results") or [])
        if v.get("link")
    ]


def norm_lens(data: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "title": m.get("title", ""),
            "link": m.get("link", ""),
            "snippet": m.get("snippet", ""),
            "source": m.get("source", ""),
            "thumbnail": m.get("thumbnail", ""),
            "engine": "google_lens",
        }
        for m in (data.get("visual_matches") or [])
        if m.get("link")
    ]


def parse_trend(data: dict[str, Any]) -> dict[str, Any] | None:
    rows = (data.get("interest_over_time") or {}).get("timeline_data") or []
    points = []
    for row in rows:
        values = row.get("values") or []
        if not values:
            continue
        raw = values[0].get("extracted_value", values[0].get("value"))
        try:
            points.append({"date": str(row.get("date", "")), "value": int(raw)})
        except (TypeError, ValueError):
            continue
    if not points:
        return None
    top = max(p["value"] for p in points)
    peak = max(points, key=lambda p: p["value"])
    first = next((p for p in points if top and p["value"] >= 0.5 * top), None)
    return {"points": points, "peak": peak["date"], "first_rise": first["date"] if first else None}


def _unique(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out = []
    for it in items:
        if it["link"] not in seen:
            seen.add(it["link"])
            out.append(it)
    return out


# -- main entry point ---------------------------------------------------------------
def run_check(
    client: Any,
    text: str,
    image_url: str,
    settings: Settings,
    use_trends: bool = True,
    use_youtube: bool = True,
) -> dict[str, Any]:
    started = time.time()
    text = (text or "").strip()[: settings.max_text_chars]
    extraction = (
        extract_claims(text, settings)
        if text
        else {"claims": [], "language": "en", "method": "none", "trend_keyword": ""}
    )
    claims, language = extraction["claims"], extraction["language"]
    hl = "hi" if language == "hi" else "en"

    errors: list[str] = []
    queries: list[dict[str, str]] = []
    credits_before = client.credits_used

    def call(engine: str, **params: Any) -> dict[str, Any]:
        try:
            data = client.search(engine, **params)
            shown = {k: str(v) for k, v in params.items() if k in ("q", "search_query", "url")}
            queries.append({"engine": engine, **shown})
            return data
        except SerpError as exc:
            errors.append(str(exc))
            return {}

    web: list[dict[str, Any]] = []
    news: list[dict[str, Any]] = []
    videos: list[dict[str, Any]] = []
    trend = None

    if claims:
        primary = claims[0]["query"]
        web += norm_web(call("google", q=f"{primary} fact check", hl=hl, gl="in"))
        news += norm_news(call("google_news", q=primary, hl=hl, gl="in"))
        if len(claims) > 1:
            web += norm_web(call("google", q=f"{claims[1]['query']} fact check", hl=hl, gl="in"))
        if use_youtube:
            videos = norm_videos(call("youtube", search_query=primary))
        if use_trends and extraction["trend_keyword"]:
            trend = parse_trend(
                call("google_trends", q=extraction["trend_keyword"], data_type="TIMESERIES", date="today 12-m", geo="IN")
            )

    image = None
    if image_url:
        lens = norm_lens(call("google_lens", url=image_url))
        image = analyse_image(lens, date.today().year)

    claim_tokens: set[str] = set()
    for c in claims:
        claim_tokens |= set(tokens(c["query"]))

    items = _unique(web + news)
    for it in items:
        classify_item(it, claim_tokens)
    assessment = assess(items, image)

    for v in videos:
        classify_item(v, claim_tokens)
        v["stance"] = (
            "debunks" if has_term(v["title"], DEBUNK_TERMS)
            else "spreading" if v.get("overlap", 0) >= 0.4
            else "related"
        )

    verdict = assessment["verdict"]
    return {
        "verdict": verdict,
        "label": assessment["label"],
        "headline": HEADLINES[verdict],
        "confidence": assessment["confidence"],
        "confidence_label": assessment["confidence_label"],
        "reasons": assessment["reasons"],
        "conflict": assessment["conflict"],
        "scores": {"debunk": assessment["debunk_score"], "support": assessment["support_score"]},
        "claims": claims,
        "language": language,
        "extraction_method": extraction["method"],
        "reply": build_reply(verdict, language, assessment),
        "refuting": assessment["refuting"],
        "supporting": assessment["supporting"],
        "evidence": {
            "web": [i for i in items if i["engine"] == "google"][:8],
            "news": [i for i in items if i["engine"] == "google_news"][:6],
            "videos": videos[:5],
            "image": (
                {k: image[k] for k in ("flagged", "earliest_year", "possibly_recycled", "notes")}
                | {"matches": image["matches"][:8]}
                if image else None
            ),
            "trend": trend,
        },
        "queries": queries,
        "errors": errors,
        "credits_used": client.credits_used - credits_before,
        "elapsed_ms": int((time.time() - started) * 1000),
    }
