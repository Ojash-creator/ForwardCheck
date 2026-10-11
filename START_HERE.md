# START HERE: from zip to submitted in ~20 minutes

Everything is built. You only need to add **your own** details. Placeholders all look like `YOUR_...` so they are easy to find.

## 1. Add your SerpApi key (2 min)

1. Create a free account at https://serpapi.com and copy your key from https://serpapi.com/manage-api-key
2. In the project folder: `cp .env.example .env` (Windows: `copy .env.example .env`)
3. Open `.env` and replace `your_serpapi_key_here` with your key.

`.env` is git-ignored. **Never paste your key into any other file or into GitHub.**

## 2. Run it and test (5 min)

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000. Run 3–4 real forwards you have received (text, and one with a public image URL). Fix nothing unless something is broken.

**Record real demo data** (optional but impressive, ~5 credits each) so the demo is replayable without credits:

```bash
python -m scripts.record_demo --id my-hoax --title "My hoax" --text "<paste a real forward>"
```

## 3. Fill in your details (3 min)

Replace every `YOUR_...` placeholder. To list them all:

```bash
python scripts/check_placeholders.py
```

Typical ones: `YOUR_GITHUB_USERNAME`, `Ojashwini Dubey`, `YOUR_DEMO_VIDEO_URL`.

## 4. Push to GitHub (5 min)

Follow `docs/GITHUB_SETUP.md`. The repo must be **public**.

## 5. Record the demo (≤ 3 min)

Follow `docs/DEMO_SCRIPT.md`. Run the app locally while recording. Upload as an unlisted YouTube video or a shareable Drive link.

## 6. Submit on the hackathon website (5 min)

Sign in with GitHub, then copy the ready-made text from `docs/SUBMISSION.md`. Submit **before the deadline: October 12, 2026, 23:59 IST.** Don't wait for the last hour.
