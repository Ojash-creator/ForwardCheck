"""Runtime settings, read from environment variables (or a local .env file)."""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

PLACEHOLDER_KEYS = {"", "your_serpapi_key_here"}


@dataclass(frozen=True)
class Settings:
    serpapi_key: str = ""
    anthropic_key: str = ""
    llm_model: str = "claude-sonnet-5-5"
    demo_mode: str = "auto"  # auto | true | false
    cache_dir: str = ".cache"
    max_credits: int = 120
    max_text_chars: int = 2000

    @property
    def has_serpapi_key(self) -> bool:
        return self.serpapi_key.strip() not in PLACEHOLDER_KEYS

    @property
    def live_enabled(self) -> bool:
        """Live SerpApi searches are allowed (key present and DEMO_MODE is not forced on)."""
        return self.has_serpapi_key and self.demo_mode.lower() != "true"

    @property
    def has_llm(self) -> bool:
        return bool(self.anthropic_key.strip())


def load_settings() -> Settings:
    load_dotenv()

    def env(name: str, default: str = "") -> str:
        return os.getenv(name, default).strip()

    try:
        max_credits = int(env("MAX_CREDITS_PER_SESSION", "120"))
    except ValueError:
        max_credits = 120

    return Settings(
        serpapi_key=env("SERPAPI_API_KEY"),
        anthropic_key=env("ANTHROPIC_API_KEY"),
        llm_model=env("LLM_MODEL", "claude-sonnet-5-5") or "claude-sonnet-5-5",
        demo_mode=env("DEMO_MODE", "auto") or "auto",
        cache_dir=env("CACHE_DIR", ".cache") or ".cache",
        max_credits=max_credits,
    )
