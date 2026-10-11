# Demo script (target: 2 min 30 s, hard limit 3 min)

The judges only need to see it **working**. Video quality does not affect judging, so a plain screen recording is enough. Record with the app running **locally** (OBS, Loom, or your OS recorder).

Before recording: use **live mode** with your key, and have two real inputs ready (a text hoax you have received, and a recycled photo with a public image URL). Do one dry run first so results are in the cache and the take is fast. If a live result looks weak, use a recorded fixture instead (`scripts/record_demo.py`).

| Time | Show | Say (adapt to your own words) |
|---|---|---|
| 0:00-0:20 | Title / empty app | "Family WhatsApp groups are where misinformation spreads fastest, and it's awkward to say 'this is fake' without proof. ForwardCheck checks a forward for you using live SerpApi search data." |
| 0:20-1:05 | Paste the **text hoax**, click Check | "I paste a real chain message. ForwardCheck extracts the claim and searches Google and Google News through SerpApi." Show the verdict, confidence and reasons. "It tells me *why*: fact-checkers covered it and news outlets call it a hoax." |
| 1:05-1:30 | Scroll evidence + reply | "Sources are tiered: fact-checkers, official, news. And here's a polite reply with links I can send straight back to the group." Click **Copy reply**. |
| 1:30-2:10 | Paste the **recycled image**, click Check | "Now an image. SerpApi's Google Lens finds where this photo appeared before." Point to the earlier-year note. "This 'live flood' photo is from an older event." (Say what your own result actually shows.) |
| 2:10-2:30 | Trends + YouTube panels, "How this was computed" | "Trends shows when the claim spiked; YouTube shows who is spreading or debunking it. Five SerpApi engines feed one verdict." |
| 2:30-2:45 | Show the unverified/conflict case if you have one | "When sources disagree, it shows both sides instead of guessing." |
| 2:45-3:00 | README / repo page | "Open source on GitHub with setup steps and tests. Thanks!" |

## Tips

- Narrate **what the real result shows**. Don't claim a feature worked if it didn't in your take.
- Keep the terminal visible for one second at the start to prove it runs locally (`uvicorn app.main:app`).
- Hide your API key: never show `.env` on screen.
- Export as MP4, upload as **unlisted** YouTube or a Drive link set to "anyone with the link", and open it in a private window to confirm it plays.
