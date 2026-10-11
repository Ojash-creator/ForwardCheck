# Publish to GitHub

The hackathon needs a **public** repository with setup instructions (the README has them).

## Option A: GitHub website + git (works everywhere)

1. Go to https://github.com/new
2. Repository name: `forwardcheck`. Set it to **Public**. Do **not** add a README, .gitignore or license (they already exist). Click *Create repository*.
3. In the unzipped project folder:

```bash
git init
git add .
git status            # confirm .env is NOT listed (only .env.example should be)
git commit -m "Initial commit: ForwardCheck"
git branch -M main
git remote add origin https://github.com/Ojash-creator/ForwardCheck.git
git push -u origin main
```

## Option B: GitHub CLI

```bash
git init && git add . && git commit -m "Initial commit: ForwardCheck"
gh repo create forwardcheck --public --source=. --push
```

## Before you push: safety check

```bash
python scripts/check_placeholders.py
```

It lists any `YOUR_...` placeholders still to fill and warns if something looks like a real API key.

**If you ever push a key by accident:** delete/rotate it immediately at https://serpapi.com/manage-api-key. Removing it in a later commit does not remove it from history.

## After pushing

- Open the repo in a private/incognito window to confirm it is public and the README renders (the Mermaid diagram should draw).
- Optional: add a screenshot to the README (`docs/screenshot.png` + `![ForwardCheck](docs/screenshot.png)`), and add topics: `serpapi`, `fact-checking`, `fastapi`, `hackathon`.
- Copy the repo URL into the hackathon form and into `README.md` / `docs/SUBMISSION.md`.
