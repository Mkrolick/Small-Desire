from persona.prompt_template import gpt_structure as gs


def test_chatgpt_request_delegates(monkeypatch):
    monkeypatch.setattr(gs.provider_client, "chat_completion", lambda *a, **k: "OUT")
    assert gs.ChatGPT_request("p") == "OUT"


def test_chatgpt_request_error_contract(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("net down")
    monkeypatch.setattr(gs.provider_client, "chat_completion", boom)
    assert gs.ChatGPT_request("p") == "ChatGPT ERROR"


def test_gpt_request_error_contract(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("net down")
    monkeypatch.setattr(gs.provider_client, "chat_completion", boom)
    assert gs.GPT_request("p", {"max_tokens": 10, "temperature": 0.5, "stop": None}) == "TOKEN LIMIT EXCEEDED"


def test_get_embedding_blank_coercion(monkeypatch):
    seen = {}
    def fake(text):
        seen["t"] = text
        return [0.0]
    monkeypatch.setattr(gs.provider_client, "get_embedding", fake)
    gs.get_embedding("")
    assert seen["t"] == "this is blank"
