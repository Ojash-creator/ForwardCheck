# Submission pack (copy-paste ready)

Fill the `YOUR_...` items, then paste into the hackathon form.

## Basics

- **Project name:** ForwardCheck
- **Tagline:** Paste a WhatsApp forward, get a verdict backed by live search evidence and a polite reply to send back.
- **Track:** Pick the closest option on the submission form. The page does not list track names in what I could see, so choose whichever is nearest to *research / verification* or *everyday tools*.
- **Repository:** https://github.com/Ojash-creator/ForwardCheck
- **Demo video:** YOUR_DEMO_VIDEO_URL
- **Team:** Ojashwini Dubey (solo) / add teammates here, up to five

## Short description (≈ 60 words)

ForwardCheck helps people verify viral WhatsApp forwards in English, Hindi and Hinglish. It extracts the claim, then uses SerpApi's Google, News, Lens, YouTube and Trends data to find fact-checks, credible coverage, image origins and spread. A transparent scoring system produces a verdict (Likely false, Misleading, Unverified, Supported) with reasons, plus a shareable reply with sources.

## Full description

**The problem.** Misinformation spreads fastest in family WhatsApp groups, where it is socially awkward to say "this is fake" without proof. Checking manually means opening many tabs and knowing which sources to trust.

**The solution.** ForwardCheck automates the checking and shows its work:

1. Extracts the checkable claim(s) from the message (Claude if available, a rule-based fallback otherwise).
2. Searches fact-checkers and the web, news coverage, and, if an image is attached, reverse image matches.
3. Tiers every source (fact-checker, official, news, other), discards results that do not match the claim, and counts each domain once.
4. Produces a verdict with a confidence level and plain-language reasons. When credible sources disagree, it shows both sides instead of hiding the conflict.
5. Drafts a short, polite reply with 2-3 source links, in Hindi or English, ready to send back.

**Why it is useful.** It targets a real, India-wide problem and gives non-technical users something they can act on in seconds.

**Honest limits.** It aggregates search results and is not a substitute for professional fact-checkers. Lens needs a public image URL. Keyword-based debunk detection can miss unusual phrasing.

## How SerpApi is used (core, not decorative)

| Engine | Used for |
|---|---|
| `google` | Searches `"<claim> fact check"` to surface fact-checkers, official clarifications and the claim's own spread |
| `google_news` | Credible coverage of the claim (confirming or debunking) |
| `google_lens` | Image provenance: fact-check pages and earlier-year matches for a photo |
| `youtube` | Videos spreading or debunking the claim |
| `google_trends` | Search interest over 12 months to show when the claim spiked |

Without SerpApi data there is no evidence to score, so no verdict. All five engines feed the final result.

## Technical highlights (for "technical complexity")

- Multi-engine orchestration with graceful degradation: one failed search never breaks a check.
- Explainable, unit-tested scoring (source tiers, topic-overlap gating, per-domain dedupe, conflict detection).
- Disk cache, hard credit cap and API-key scrubbing in error messages.
- Hindi/Devanagari-aware tokenisation and Hindi reply templates.
- Offline test suite (31 tests) and a script to record real SerpApi responses for replayable demos.

## AI tools used

Claude (Anthropic) assisted with code generation and documentation; I reviewed and take responsibility for every component. Claude is also an optional runtime dependency for claim extraction.

## Pre-submission checklist

- [ ] SerpApi account created, key works locally
- [ ] App tested with 3-4 real forwards (one with an image URL)
- [ ] `python scripts/check_placeholders.py` reports "All clear"
- [ ] `.env` is **not** in the GitHub repo
- [ ] GitHub repo is **public** and README renders correctly
- [ ] Demo video ≤ 3 min, shows the app **running locally**, link opens when logged out
- [ ] Submitted via the website before **Oct 12, 2026, 23:59 IST**
