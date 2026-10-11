"""Record REAL SerpApi responses into a demo fixture, so judges can replay them without credits.

Usage (needs SERPAPI_API_KEY in .env; costs about 5 credits):

    python -m scripts.record_demo --id my-hoax --title "My hoax" \
        --text "pasted forward text ..." [--image-url https://.../photo.jpg]

Writes demo/<id>.json. Restart the server and it appears as an example chip.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.config import load_settings
from app.pipeline import run_check
from app.serp import SerpClient


class RecordingClient(SerpClient):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.recorded: dict = {}

    def search(self, engine, **params):
        data = super().search(engine, **params)
        self.recorded.setdefault(engine, data)
        return data


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--id", required=True, help="slug, e.g. my-hoax")
    p.add_argument("--title", required=True)
    p.add_argument("--text", default="")
    p.add_argument("--image-url", default="")
    p.add_argument("--description", default="Recorded from live SerpApi results.")
    args = p.parse_args()

    settings = load_settings()
    if not settings.has_serpapi_key:
        print("Set SERPAPI_API_KEY in .env first.", file=sys.stderr)
        return 1

    client = RecordingClient(settings.serpapi_key, settings.cache_dir, settings.max_credits)
    result = run_check(client, args.text, args.image_url, settings)
    fixture = {
        "example": {
            "id": args.id, "title": args.title, "description": args.description,
            "text": args.text, "image_url": args.image_url,
        },
        "_note": "Real SerpApi responses recorded with scripts/record_demo.py.",
        "responses": client.recorded,
    }
    out = Path(__file__).resolve().parent.parent / "demo" / f"{args.id}.json"
    out.write_text(json.dumps(fixture, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Verdict: {result['label']} ({result['confidence']}%) | credits used: {result['credits_used']}")
    print(f"Saved {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
