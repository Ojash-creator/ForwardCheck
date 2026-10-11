import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app
from app.pipeline import run_check
from app.serp import DemoClient, SerpClient, SerpError

DEMO = Path(__file__).resolve().parent.parent / "demo"


def fixture(name):
    return json.loads((DEMO / f"{name}.json").read_text(encoding="utf-8"))


def run(name):
    fx = fixture(name)
    ex = fx["example"]
    return run_check(DemoClient(fx), ex["text"], ex.get("image_url", ""), Settings())


def test_chain_hoax_is_likely_false():
    out = run("whatsapp-block")
    assert out["verdict"] == "likely_false"
    assert out["credits_used"] == 0
    assert "demo-factcheck.example" in out["reply"]
    assert out["evidence"]["trend"]["peak"]
    assert any(v["stance"] == "debunks" for v in out["evidence"]["videos"])


def test_recycled_image_is_flagged():
    out = run("flood-photo")
    assert out["verdict"] in {"likely_false", "misleading"}
    img = out["evidence"]["image"]
    assert img["possibly_recycled"] and img["earliest_year"] == 2018


def test_genuine_alert_is_supported():
    out = run("rain-alert")
    assert out["verdict"] == "supported"
    assert out["reply"].count("•") >= 1


def test_search_failures_degrade_gracefully():
    class Broken:
        credits_used = 0

        def search(self, engine, **params):
            raise SerpError(f"{engine}: boom")

    out = run_check(Broken(), "Government will ban all 500 rupee notes tomorrow", "", Settings())
    assert out["verdict"] == "unverified"
    assert out["errors"]


def test_api_key_never_leaks_in_errors():
    import requests

    class Boom(requests.Session):
        def get(self, url, params=None, timeout=None):
            raise requests.ConnectionError(f"failed for {url}?api_key={params['api_key']}")

    client = SerpClient("SECRET123", cache_dir="/tmp/fc-test-cache", session=Boom())
    with pytest.raises(SerpError) as exc:
        client.search("google", q="x unique query for no cache hit 1")
    assert "SECRET123" not in str(exc.value)


def test_credit_cap_blocks_extra_calls(tmp_path):
    client = SerpClient("k", cache_dir=str(tmp_path), max_credits=0)
    with pytest.raises(SerpError):
        client.search("google", q="anything")


web = TestClient(app)


def test_api_health_and_examples():
    assert web.get("/api/health").json()["samples"] >= 3
    assert len(web.get("/api/examples").json()) >= 3


def test_api_sample_check():
    r = web.post("/api/check", json={"example_id": "whatsapp-block", "use_sample": True})
    assert r.status_code == 200 and r.json()["mode"] == "sample"


def test_api_validation():
    assert web.post("/api/check", json={}).status_code == 400
    assert web.post("/api/check", json={"text": "x", "image_url": "javascript:alert(1)"}).status_code == 400


def test_homepage_served():
    r = web.get("/")
    assert r.status_code == 200 and "ForwardCheck" in r.text


class FakeResponse:
    def __init__(self, status, payload):
        self.status_code, self._payload = status, payload

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, *responses):
        self.responses, self.calls = list(responses), 0

    def get(self, url, params=None, timeout=None):
        self.calls += 1
        return self.responses.pop(0)


def test_live_client_success_cache_hit_and_empty_result(tmp_path):
    ok = FakeResponse(200, {"organic_results": [{"title": "t", "link": "https://x.com"}], "search_parameters": {"q": "x"}})
    empty = FakeResponse(200, {"error": "Google hasn't returned any results for this query."})
    sess = FakeSession(ok, empty)
    client = SerpClient("k", cache_dir=str(tmp_path), session=sess)

    first = client.search("google", q="one")
    assert first["organic_results"] and "search_parameters" not in first
    assert client.credits_used == 1

    client.search("google", q="one")          # served from disk cache
    assert sess.calls == 1 and client.credits_used == 1

    assert client.search("google", q="two") == {}   # empty result is not an error
    assert client.credits_used == 2


def test_live_client_reports_bad_key_without_leaking_it(tmp_path):
    client = SerpClient("SECRET123", cache_dir=str(tmp_path), session=FakeSession(FakeResponse(401, {"error": "Invalid API key"})))
    with pytest.raises(SerpError) as exc:
        client.search("google", q="three")
    assert "401" in str(exc.value) and "SECRET123" not in str(exc.value)
