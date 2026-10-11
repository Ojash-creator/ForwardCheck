"""FastAPI app. Run with:  uvicorn app.main:app --reload"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import __version__
from .config import load_settings
from .pipeline import run_check
from .serp import DemoClient, SerpClient

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"
DEMO_DIR = ROOT / "demo"

settings = load_settings()
live_client = (
    SerpClient(settings.serpapi_key, settings.cache_dir, settings.max_credits)
    if settings.live_enabled
    else None
)


def load_fixtures() -> dict[str, dict[str, Any]]:
    fixtures: dict[str, dict[str, Any]] = {}
    for path in sorted(DEMO_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            fixtures[data["example"]["id"]] = data
        except (OSError, ValueError, KeyError):
            continue
    return fixtures


FIXTURES = load_fixtures()

app = FastAPI(title="ForwardCheck", version=__version__)


class CheckRequest(BaseModel):
    text: str = Field(default="", max_length=5000)
    image_url: str = Field(default="", max_length=2000)
    example_id: str | None = None
    use_sample: bool = False
    use_trends: bool = True
    use_youtube: bool = True


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "version": __version__,
        "live": settings.live_enabled,
        "llm": settings.has_llm,
        "samples": len(FIXTURES),
        "credits_used": live_client.credits_used if live_client else 0,
        "credit_cap": settings.max_credits,
    }


@app.get("/api/examples")
def examples() -> list[dict[str, Any]]:
    return [f["example"] for f in FIXTURES.values()]


@app.post("/api/check")
def check(req: CheckRequest) -> dict[str, Any]:
    text, image_url = req.text.strip(), req.image_url.strip()

    if req.use_sample:
        fixture = FIXTURES.get(req.example_id or "")
        if not fixture:
            raise HTTPException(400, "Pick one of the built-in examples to use sample data.")
        client: Any = DemoClient(fixture)
        text, image_url = fixture["example"]["text"], fixture["example"].get("image_url", "")
        mode = "sample"
    else:
        if not live_client:
            raise HTTPException(
                400,
                "Live mode needs SERPAPI_API_KEY in your .env file. "
                "Until then, pick an example and tick 'Use saved sample data'.",
            )
        client, mode = live_client, "live"

    if not text and not image_url:
        raise HTTPException(400, "Paste the forwarded message text, an image URL, or both.")
    if image_url:
        parsed = urlparse(image_url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise HTTPException(400, "Image URL must be a public http(s) link (Google Lens fetches it).")

    result = run_check(client, text, image_url, settings, req.use_trends, req.use_youtube)
    result["mode"] = mode
    return result


app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")
