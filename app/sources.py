"""Source lists used for credibility tiers. Edit these to tune the verdicts.

The lists are deliberately short and opinionated: they are a starting point, not a
definitive ranking of every outlet. Domains ending in `.example` are used only by the
synthetic demo fixtures in /demo.
"""

# Dedicated fact-checking organisations (IFCN signatories and well-known units).
FACTCHECK_DOMAINS = {
    "altnews.in", "boomlive.in", "factchecker.in", "newschecker.in", "vishvasnews.com",
    "factly.in", "newsmeter.in", "dfrac.org", "factcrescendo.com",
    "snopes.com", "politifact.com", "factcheck.org", "fullfact.org",
    "factcheck.afp.com", "leadstories.com",
    "demo-factcheck.example",
}

# Official / government / intergovernmental sources.
GOV_SUFFIXES = (".gov.in", ".nic.in", ".gov", ".gov.uk")
GOV_DOMAINS = {"who.int", "un.org", "rbi.org.in", "demo-gov.example"}

# Established news organisations.
NEWS_DOMAINS = {
    "thehindu.com", "indianexpress.com", "hindustantimes.com", "ndtv.com",
    "timesofindia.indiatimes.com", "indiatoday.in", "livemint.com",
    "economictimes.indiatimes.com", "thewire.in", "scroll.in", "theprint.in",
    "deccanherald.com", "tribuneindia.com", "telegraphindia.com", "news18.com",
    "aajtak.in", "thequint.com", "ptinews.com", "aninews.in",
    "bbc.com", "bbc.co.uk", "reuters.com", "apnews.com", "aljazeera.com",
    "theguardian.com", "nytimes.com", "washingtonpost.com",
    "demo-news.example",
}

# Google News sometimes returns news.google.com redirect links; fall back to the outlet name.
NEWS_NAMES = (
    "the hindu", "indian express", "hindustan times", "ndtv", "times of india", "india today",
    "livemint", "economic times", "the wire", "scroll", "theprint", "deccan herald",
    "tribune", "telegraph", "news18", "aaj tak", "the quint", "pti", "ani",
    "bbc", "reuters", "associated press", "al jazeera", "the guardian",
    "new york times", "washington post",
)
FACTCHECK_NAMES = (
    "alt news", "boom", "newschecker", "vishvas news", "factly", "newsmeter", "dfrac",
    "snopes", "politifact", "factcheck.org", "full fact", "afp fact check", "lead stories",
    "pib fact check", "fact crescendo",
)
GOV_NAMES = ("pib", "press information bureau", "india meteorological", "world health organization")

# URL path fragments that mark a fact-check section on a general news site.
FACTCHECK_PATH_HINTS = ("fact-check", "factcheck", "webqoof", "vishvas")

# Language that signals a claim is being debunked.
DEBUNK_TERMS = (
    "fake", "false", "misleading", "hoax", "debunk", "no evidence", "not true", "baseless",
    "unrelated", "old video", "old photo", "old image", "old picture", "recycled", "misattributed",
    "satire", "clarif", "scam", "rumour", "rumor", "misinformation", "no such order",
    "not blocking", "never said", "is a lie",
    # Hindi / Hinglish
    "फर्जी", "झूठ", "भ्रामक", "अफवाह", "गलत दावा", "पुराना वीडियो", "पुरानी तस्वीर", "फैक्ट चेक में",
    "jhooth", "afwah", "galat",
)

# Language that signals a fact-checker rated the claim as true.
CONFIRM_TERMS = (
    "claim is true", "is true", "confirmed", "genuine", "verified", "is correct", "सच है", "सही है",
)
