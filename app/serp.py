"""Thin SerpApi client with disk caching, a credit cap and a no-network demo client.

SerpApi docs: https://serpapi.com/search-api
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import requests

ENDPOINT = "https://serpapi.com/search.json"
CACHE_TTL_SECONDS = 24 * 3600


class SerpError(RuntimeError):
    """Raised for any problem talking to SerpApi (message is safe to show to users)."""


class SerpClient:
    """Live client. Every uncached call costs one SerpApi search credit."""

    def __init__(
        self,
        api_key: str,
        cache_dir: str = ".cache",
        max_credits: int = 120,
        timeout: int = 30,
        session: requests.Session | None = None,
    ) -> None:
        self.api_key = api_key
        self.cache_dir = Path(cache_dir)
        self.max_credits = max_credits
        self.timeout = timeout
        self.session = session or requests.Session()
        self.credits_used = 0

    # -- helpers ---------------------------------------------------------
    def _cache_path(self, engine: str, params: dict[str, Any]) -> Path:
        blob = json.dumps({"engine": engine, **params}, sort_keys=True, ensure_ascii=False)
        return self.cache_dir / f"{hashlib.sha256(blob.encode('utf-8')).hexdigest()[:32]}.json"

    def _scrub(self, message: str) -> str:
        """Never leak the API key in error messages (requests puts the URL in them)."""
        return message.replace(self.api_key, "***") if self.api_key else message

    # -- public API ------------------------------------------------------
    def search(self, engine: str, **params: Any) -> dict[str, Any]:
        path = self._cache_path(engine, params)
        try:
            if path.exists() and time.time() - path.stat().st_mtime < CACHE_TTL_SECONDS:
                return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass  # a corrupt cache file just means we fetch again

        if self.credits_used >= self.max_credits:
            raise SerpError(
                f"Credit cap reached ({self.max_credits} searches this session). "
                "Raise MAX_CREDITS_PER_SESSION in .env if this is intentional."
            )

        try:
            resp = self.session.get(
                ENDPOINT,
                params={"engine": engine, "api_key": self.api_key, **params},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise SerpError(f"Network error calling SerpApi ({engine}): {self._scrub(str(exc))}") from None

        if resp.status_code == 401:
            raise SerpError("SerpApi rejected the API key (HTTP 401). Check SERPAPI_API_KEY in .env.")
        if resp.status_code == 429:
            raise SerpError("SerpApi rate or credit limit reached (HTTP 429).")

        try:
            data = resp.json()
        except ValueError:
            raise SerpError(f"SerpApi returned a non-JSON response for {engine} (HTTP {resp.status_code}).") from None

        error = data.get("error") if isinstance(data, dict) else None
        if resp.status_code != 200 or error:
            message = str(error or f"HTTP {resp.status_code}")
            if "hasn't returned any results" in message.lower() or "no results" in message.lower():
                data = {}  # an empty result set is a normal outcome, not a failure
            else:
                raise SerpError(f"{engine}: {self._scrub(message)}")

        self.credits_used += 1
        if isinstance(data, dict):
            data.pop("search_parameters", None)
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass  # caching is best-effort
        return data


class DemoClient:
    """Serves pre-saved responses from a demo fixture. Makes no network calls, costs no credits."""

    credits_used = 0

    def __init__(self, fixture: dict[str, Any]) -> None:
        self.responses: dict[str, Any] = fixture.get("responses", {})

    def search(self, engine: str, **params: Any) -> dict[str, Any]:
        return self.responses.get(engine, {})
