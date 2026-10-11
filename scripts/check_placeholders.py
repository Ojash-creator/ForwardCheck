"""Pre-submission check: finds unfilled YOUR_* placeholders and accidentally committed secrets.

Run:  python scripts/check_placeholders.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", ".cache", "__pycache__", ".venv", "venv", ".pytest_cache"}
TEXT_EXT = {".md", ".py", ".txt", ".html", ".json", ".example", ".toml", ".yml", ".yaml", ""}
PLACEHOLDER = re.compile(r"YOUR_[A-Z_]+")
KEY_LIKE = re.compile(r"(?:SERPAPI_API_KEY|ANTHROPIC_API_KEY)\s*=\s*([A-Za-z0-9_\-]{20,})")


def main() -> int:
    problems = 0
    if (ROOT / ".env").exists():
        print("NOTE: .env exists locally. It is git-ignored; make sure it never gets committed.")
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.parts):
            continue
        # START_HERE.md only *describes* the placeholders; it is not something to fill in.
        if path.name in {"check_placeholders.py", "START_HERE.md"} or path.suffix not in TEXT_EXT:
            continue
        if path.name == ".env":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(ROOT)
        for m in PLACEHOLDER.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            print(f"TODO  {rel}:{line}  {m.group(0)}")
            problems += 1
        for m in KEY_LIKE.finditer(text):
            if path.name != ".env.example":
                print(f"DANGER  {rel}: looks like a real API key. Remove it!")
                problems += 1
    print(f"\n{problems} item(s) to fix." if problems else "\nAll clear. Ready to push.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
