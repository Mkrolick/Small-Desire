import pytest
from persona.prompt_template import provider_client as pc


class _Resp:
    def __init__(self, status_code, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text
    def json(self):
        return self._payload
    def raise_for_status(self):
        pass


def test_chat_completion_returns_content_and_sends_passthrough(monkeypatch):
    captured = {}
    def fake_post(url, json, headers, timeout):
        captured["url"] = url
        captured["json"] = json
        return _Resp(200, {"choices": [{"message": {"content": "hi there"}}]})
    monkeypatch.setattr(pc.requests, "post", fake_post)
    out = pc.chat_completion("hello")
    assert out == "hi there"
    assert captured["url"].endswith("/chat/completions")
    assert captured["json"]["messages"][0]["content"] == "hello"
    assert captured["json"]["raw_passthrough"] is True


def test_get_embedding_returns_bare_float_list(monkeypatch):
    monkeypatch.setattr(pc.requests, "post",
                        lambda url, json, headers, timeout: _Resp(200, {"data": [{"embedding": [0.1, 0.2, 0.3]}]}))
    v = pc.get_embedding("cat")
    assert v == [0.1, 0.2, 0.3]
    assert isinstance(v, list)


def test_post_with_retry_backs_off_then_succeeds(monkeypatch):
    calls = {"n": 0}
    def fake_post(url, json, headers, timeout):
        calls["n"] += 1
        return _Resp(200, {"ok": True}) if calls["n"] >= 2 else _Resp(503, text="busy")
    monkeypatch.setattr(pc.requests, "post", fake_post)
    monkeypatch.setattr(pc.time, "sleep", lambda s: None)
    assert pc._post_with_retry("http://x", {}, {}, max_attempts=3) == {"ok": True}
    assert calls["n"] == 2


def test_post_with_retry_fails_fast_on_4xx(monkeypatch):
    calls = {"n": 0}
    def fake_post(url, json, headers, timeout):
        calls["n"] += 1
        return _Resp(400, text="bad request")
    monkeypatch.setattr(pc.requests, "post", fake_post)
    monkeypatch.setattr(pc.time, "sleep", lambda s: None)
    with pytest.raises(RuntimeError):
        pc._post_with_retry("http://x", {}, {}, max_attempts=3)
    assert calls["n"] == 1  # non-retryable 4xx: no retry


def test_chat_completion_passes_optional_params(monkeypatch):
    captured = {}
    def fake_post(url, json, headers, timeout):
        captured["json"] = json
        return _Resp(200, {"choices": [{"message": {"content": "x"}}]})
    monkeypatch.setattr(pc.requests, "post", fake_post)
    pc.chat_completion("p", max_tokens=256, temperature=0.3, stop=["END"])
    assert captured["json"]["max_tokens"] == 256
    assert captured["json"]["temperature"] == 0.3
    assert captured["json"]["stop"] == ["END"]


def test_chat_completion_omits_unset_optional_params(monkeypatch):
    captured = {}
    def fake_post(url, json, headers, timeout):
        captured["json"] = json
        return _Resp(200, {"choices": [{"message": {"content": "x"}}]})
    monkeypatch.setattr(pc.requests, "post", fake_post)
    pc.chat_completion("p")
    assert "max_tokens" not in captured["json"]
    assert "temperature" not in captured["json"]
    assert "stop" not in captured["json"]
