from app.scoring import analyse_image, assess, build_reply, classify_item, domain_of, tier_of

TOKENS = {"whatsapp", "blocked", "forward", "contacts", "government", "order"}


def mk(title, link, snippet="", source=""):
    return classify_item({"title": title, "link": link, "snippet": snippet, "source": source}, TOKENS)


def test_domain_and_tiers():
    assert domain_of("https://www.altnews.in/x") == "altnews.in"
    assert tier_of("altnews.in") == "factcheck"
    assert tier_of("pib.gov.in") == "gov"
    assert tier_of("thehindu.com", "https://thehindu.com/news/x") == "news"
    assert tier_of("thehindu.com", "https://thehindu.com/fact-check/x") == "factcheck"
    assert tier_of("random-blog.com") == "other"


def test_google_news_redirect_uses_source_name():
    assert tier_of("news.google.com", "https://news.google.com/read/abc", "The Hindu") == "news"
    assert tier_of("news.google.com", "https://news.google.com/read/abc", "Alt News") == "factcheck"


def test_likely_false_from_factchecker_plus_news():
    items = [
        mk("Fact check: WhatsApp blocked claim is false", "https://boomlive.in/a", "forward contacts government order fake"),
        mk("Hoax: WhatsApp blocked message is fake", "https://thehindu.com/b", "forward contacts government order hoax"),
    ]
    out = assess(items)
    assert out["verdict"] == "likely_false"
    assert out["confidence"] >= 70
    assert out["refuting"]


def test_supported_from_gov_and_news():
    items = [
        mk("Government confirms order", "https://pib.gov.in/x", "whatsapp blocked forward contacts government order"),
        mk("Order reported", "https://thehindu.com/y", "whatsapp blocked forward contacts government order"),
    ]
    out = assess(items)
    assert out["verdict"] == "supported"


def test_same_domain_does_not_inflate_score():
    items = [
        mk("Fake claim 1", "https://boomlive.in/a", "whatsapp blocked forward contacts fake"),
        mk("Fake claim 2", "https://boomlive.in/b", "whatsapp blocked forward contacts fake"),
        mk("Fake claim 3", "https://boomlive.in/c", "whatsapp blocked forward contacts fake"),
    ]
    assert assess(items)["debunk_score"] == 3.0  # one domain counts once


def test_no_evidence_is_unverified_with_hold_off_advice():
    out = assess([mk("Unrelated", "https://random-blog.com/x", "cats and dogs")])
    assert out["verdict"] == "unverified"
    assert any("Hold off" in r for r in out["reasons"])


def test_split_sources_are_unverified_and_flagged_as_conflict():
    items = [
        mk("Fact check: fake claim", "https://boomlive.in/a", "whatsapp blocked forward contacts fake"),
        mk("Order confirmed", "https://pib.gov.in/x", "whatsapp blocked forward contacts government order"),
        mk("Order reported", "https://thehindu.com/y", "whatsapp blocked forward contacts government order"),
    ]
    out = assess(items)
    assert out["verdict"] == "unverified"
    assert out["conflict"]


def test_fact_checker_rating_true_is_not_counted_as_debunk():
    it = mk("Fact check: claim is true", "https://boomlive.in/a", "whatsapp blocked forward contacts claim is true")
    out = assess([it])
    assert out["debunk_score"] == 0.0
    assert out["support_score"] == 2.0


def test_image_flagged_by_factchecker_and_old_year():
    matches = [
        {"title": "Fact check: photo is from 2018", "link": "https://boomlive.in/p", "snippet": "", "source": ""},
        {"title": "Flood gallery 2018", "link": "https://random.com/f", "snippet": "", "source": ""},
    ]
    img = analyse_image(matches, current_year=2026)
    assert img["flagged"] == 1 and img["earliest_year"] == 2018 and img["possibly_recycled"]
    assert img["score"] == 3.0
    assert assess([], img)["verdict"] == "likely_false"


def test_future_years_are_ignored():
    img = analyse_image([{"title": "Event 2031 plans", "link": "https://x.com/a", "snippet": "", "source": ""}], 2026)
    assert img["earliest_year"] is None


def test_reply_language_and_links():
    items = [mk("Fact check: fake", "https://boomlive.in/a", "whatsapp blocked forward contacts fake", "BOOM")]
    out = assess(items)
    en = build_reply(out["verdict"], "en", out)
    hi = build_reply(out["verdict"], "hi", out)
    assert "https://boomlive.in/a" in en and "नमस्ते" in hi
