from app.claims import detect_language, extract_claims, heuristic_claims, make_query, tokens
from app.config import Settings


def test_language_detection():
    assert detect_language("यह एक संदेश है") == "hi"
    assert detect_language("this is a message") == "en"


def test_tokens_drop_stopwords_and_keep_numbers():
    toks = tokens("The government will give Rs 5000 to all of you")
    assert "government" in toks and "5000" in toks and "the" not in toks


def test_devanagari_tokens_survive():
    assert "सरकार" in tokens("सरकार फ्री राशन दे रही है")


def test_make_query_dedupes_and_limits():
    q = make_query("alert alert alert government free ration free ration scheme today announced widely")
    assert q.split().count("alert") == 1
    assert len(q.split()) <= 9


def test_heuristic_prefers_claim_sentences_over_greetings():
    text = "Hello friends, good morning. The government has banned 500 rupee notes from tomorrow. Please share."
    claims = heuristic_claims(text)
    assert claims and "banned" in claims[0]["claim"]


def test_extract_claims_without_llm_uses_heuristic():
    out = extract_claims(
        "URGENT! WhatsApp will be blocked tomorrow unless you forward this to 10 contacts.", Settings()
    )
    assert out["method"] == "heuristic"
    assert out["claims"] and out["trend_keyword"]


def test_empty_text_returns_no_claims():
    assert extract_claims("", Settings())["claims"] == []


def test_call_to_action_is_not_picked_as_the_claim():
    text = "Shocking! This is the flood in our city right now, see how the whole city has drowned. Share so everyone is aware."
    claims = heuristic_claims(text)
    assert "flood" in claims[0]["claim"]
    assert all("everyone is aware" not in c["claim"] for c in claims)
