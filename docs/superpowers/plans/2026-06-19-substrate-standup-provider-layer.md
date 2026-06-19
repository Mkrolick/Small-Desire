# Substrate Stand-Up & Provider Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up a headless, instrumentable fork of Stanford `generative_agents` (Smallville) for two agents, with all LLM traffic routed through a provider-agnostic client (chat → TokensPLS/`gpt-5.4`, embeddings → an external provider), proven by a one-step end-to-end smoke run.

**Architecture:** Vendor the upstream backend into the SmallDesire repo unchanged except at two seams. Seam 1: replace the five `openai==0.27` call sites in `gpt_structure.py` with a small `provider_client.py` (plain `requests`, no global SDK state). Seam 2: add a `process_step()` method to `ReverieServer` so the backend can be driven in-process by a tiny feeder, with no Phaser frontend and no disk polling. A small modification to the separate TokensPLS repo adds a `raw_passthrough` mode so the proxy doesn't strip/relabel our prompts and outputs.

**Tech Stack:** Python 3.9.x, `numpy` (the only native dep the headless path actually uses), `requests`, `pytest`. TokensPLS side: FastAPI + pytest.

---

## Scope & Roadmap

This is **Plan 1 of a sequence** (the spec, `docs/superpowers/specs/2026-06-19-girardian-mimetic-doubling-smallville-design.md`, Phase 0 + Phase 1, is multi-subsystem). This plan delivers the foundation everything else builds on. Follow-on plans, each its own spec→plan cycle, are listed under **Roadmap** at the bottom and are deliberately *not* detailed here — their exact tasks depend on internals this plan makes concrete.

**Two repos are touched:**
- **SmallDesire** — `/Users/mkrolick/Documents/GitHub/SmallDesire` (this repo; the vendored fork lives here).
- **TokensPLS** — `/Users/mkrolick/Code/TokensPLS` (Group A only; a separate PR).

**Grounding facts (verified against the live code, do not re-derive):**
- Upstream pinned commit: `fe05a71d3e4ed7d10bf68aa4eda6dd995ec070f4`.
- The backend MUST run with **CWD = `generative_agents/reverie/backend_server/`** — all `utils.py` paths are relative to it.
- `reverie/backend_server/utils.py` is **gitignored upstream and absent** — we create it.
- The only third-party imports in the backend are `numpy` (7 files), `openai` (2 files — we remove), and a **dead** `from selenium import webdriver` in `reverie.py:31`.
- GA chat calls send a **single** `{"role":"user","content":prompt}` message, so TokensPLS prompt-flattening is a non-issue for us; the live risk is the **output** `strip_hallucinated_turns` mangling dialogue — that is what `raw_passthrough` disables.

---

## Prerequisites

- `git`, `python3` (3.9.x preferred; 3.9–3.11 all work since `numpy` is the only native dep), network access.
- For the **integration** smoke (Task 12 only): a running TokensPLS server and an embeddings API key. All other tests are fully offline (mocked).

---

## File Structure

**TokensPLS (`/Users/mkrolick/Code/TokensPLS`):**
| Path | Responsibility |
|---|---|
| `app/models/openai.py` | Add `raw_passthrough` field to `ChatCompletionRequest`. |
| `app/routes/openai_compat.py` | Add `format_messages_passthrough` helper; guard the inbound flatten (line 433) and outbound strip (line 626) on the flag. |
| `tests/test_openai_compat_helpers.py` | Unit tests for the new helper. |
| `tests/test_openai_compat.py` | Route tests: raw mode skips relabel + skips strip; default still strips. |

**SmallDesire (`/Users/mkrolick/Documents/GitHub/SmallDesire`):**
| Path | Responsibility |
|---|---|
| `generative_agents/` (vendored subset) | The upstream backend + maze assets + the base sim, pinned. |
| `generative_agents/reverie/backend_server/utils.py` | **Create.** Config: legacy paths + new `TOKENSPLS_*` / `EMBED_*` env-backed provider config. |
| `generative_agents/reverie/backend_server/persona/prompt_template/provider_client.py` | **Create.** `chat_completion()` + `get_embedding()` + `_post_with_retry()`. |
| `generative_agents/reverie/backend_server/persona/prompt_template/gpt_structure.py` | **Modify.** Delegate the 5 LLM functions to `provider_client`. |
| `generative_agents/reverie/backend_server/reverie.py` | **Modify.** Add `process_step()`; init `self._game_obj_cleanup`; drop dead `selenium` import. |
| `generative_agents/reverie/backend_server/headless.py` | **Create.** `run_headless()` + `next_env_from_movements()` feeder. |
| `generative_agents/environment/frontend_server/storage/base_the_ville_isabella_maria/` | **Create.** 2-agent base forked from the 3-agent base. |
| `generative_agents/reverie/backend_server/tests/` | **Create.** All pytest tests + `conftest.py`. |
| `.gitignore` | Ignore venv, `__pycache__`, `.env`, and per-run sim folders. |

---

## GROUP A — TokensPLS `raw_passthrough` mode
*(Repo: `/Users/mkrolick/Code/TokensPLS`. Run all commands with that as CWD. Verdict from grounding: the browser backend takes a single string, so "passthrough" = **faithful formatting without relabeling/stripping**, NOT structured messages — state this in the PR description.)*

### Task 1: Add the `raw_passthrough` request field

**Files:**
- Modify: `app/models/openai.py:248` (end of `ChatCompletionRequest` scalar fields)
- Test: `tests/test_openai_models.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_openai_models.py`:
```python
from app.models.openai import ChatCompletionRequest

def test_raw_passthrough_defaults_false():
    req = ChatCompletionRequest(model="gpt-5.4", messages=[{"role": "user", "content": "hi"}])
    assert req.raw_passthrough is False

def test_raw_passthrough_accepts_true():
    req = ChatCompletionRequest(
        model="gpt-5.4",
        messages=[{"role": "user", "content": "hi"}],
        raw_passthrough=True,
    )
    assert req.raw_passthrough is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./venv/bin/python -m pytest tests/test_openai_models.py -k raw_passthrough -q`
Expected: FAIL — `test_raw_passthrough_accepts_true` fails (field silently dropped; `req.raw_passthrough` raises `AttributeError`).

- [ ] **Step 3: Add the field**

In `app/models/openai.py`, immediately after line 248 (`user: Optional[str] = None`):
```python
    # SmallDesire: opt-in raw mode — no role-relabel flattening, no trailing
    # User:/Assistant: strip. Default False preserves all existing behavior.
    raw_passthrough: Optional[bool] = Field(
        default=False,
        description="If true: faithful formatting (no relabel) and no hallucinated-turn stripping.",
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./venv/bin/python -m pytest tests/test_openai_models.py -k raw_passthrough -q`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add app/models/openai.py tests/test_openai_models.py
git commit -m "feat(openai-compat): add raw_passthrough request field"
```

### Task 2: Add the `format_messages_passthrough` helper

**Files:**
- Modify: `app/routes/openai_compat.py` (new function after `format_messages_as_prompt`, ~line 152)
- Test: `tests/test_openai_compat_helpers.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_openai_compat_helpers.py`:
```python
from app.models.openai import ChatMessage
from app.routes.openai_compat import format_messages_passthrough

def test_passthrough_single_message_is_verbatim():
    msgs = [ChatMessage(role="user", content="line1\nline2")]
    assert format_messages_passthrough(msgs) == "line1\nline2"

def test_passthrough_multi_has_no_relabel_headers():
    msgs = [
        ChatMessage(role="system", content="sys"),
        ChatMessage(role="user", content="hello"),
    ]
    out = format_messages_passthrough(msgs)
    assert "System instructions:" not in out
    assert "Previous conversation:" not in out
    assert "sys" in out and "hello" in out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./venv/bin/python -m pytest tests/test_openai_compat_helpers.py -k passthrough -q`
Expected: FAIL — `ImportError: cannot import name 'format_messages_passthrough'`.

- [ ] **Step 3: Implement the helper**

In `app/routes/openai_compat.py`, directly after the `format_messages_as_prompt` function (ends ~line 152):
```python
def format_messages_passthrough(messages: list[ChatMessage]) -> str:
    """Raw mode: preserve content verbatim — no 'System instructions:' /
    'Previous conversation:' relabeling. Single message -> its content.
    Multiple -> 'role: content' joined by blank lines, nothing else added."""
    from app.models.openai import get_content_string
    if not messages:
        return ""
    if len(messages) == 1:
        return get_content_string(messages[0].content)
    return "\n\n".join(f"{m.role}: {get_content_string(m.content)}" for m in messages)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./venv/bin/python -m pytest tests/test_openai_compat_helpers.py -k passthrough -q`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add app/routes/openai_compat.py tests/test_openai_compat_helpers.py
git commit -m "feat(openai-compat): add format_messages_passthrough helper"
```

### Task 3: Gate flattening and stripping on the flag

**Files:**
- Modify: `app/routes/openai_compat.py:433` (inbound) and `:626` (outbound)
- Test: `tests/test_openai_compat.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_openai_compat.py` (uses the existing `client` / `app` / `_ok_result` fixtures at the top of that file):
```python
def _chat_body(raw, content="answer\nUser: more"):
    return {
        "model": "gpt-5.4",
        "messages": [{"role": "system", "content": "sys"}, {"role": "user", "content": "hello"}],
        "raw_passthrough": raw,
    }, content

def test_raw_passthrough_skips_relabel_in_prompt(app, client):
    body, _ = _chat_body(True)
    client.post("/v1/chat/completions", json=body)
    call = app._mock_client.send_new_conversation.call_args
    sent_text = call.kwargs.get("text") if call.kwargs.get("text") is not None else call.args[0]
    assert "System instructions:" not in sent_text
    assert "Previous conversation:" not in sent_text

def test_raw_passthrough_preserves_output(app, client):
    body, content = _chat_body(True)
    app._mock_client.send_new_conversation.return_value = _ok_result(text=content)
    r = client.post("/v1/chat/completions", json=body)
    assert r.json()["choices"][0]["message"]["content"] == "answer\nUser: more"

def test_default_still_strips_output(app, client):
    body, content = _chat_body(False)
    app._mock_client.send_new_conversation.return_value = _ok_result(text=content)
    r = client.post("/v1/chat/completions", json=body)
    assert r.json()["choices"][0]["message"]["content"] == "answer"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `./venv/bin/python -m pytest tests/test_openai_compat.py -k "raw_passthrough or default_still_strips" -q`
Expected: FAIL — `test_raw_passthrough_skips_relabel_in_prompt` and `test_raw_passthrough_preserves_output` fail (relabeling and stripping still applied).

- [ ] **Step 3: Gate the inbound flatten**

In `app/routes/openai_compat.py`, replace line 433 (`prompt = format_messages_as_prompt(request.messages)`) inside the `else:` block with:
```python
        if request.raw_passthrough:
            prompt = format_messages_passthrough(request.messages)
        else:
            prompt = format_messages_as_prompt(request.messages)
```

- [ ] **Step 4: Gate the outbound strip**

In `app/routes/openai_compat.py`, replace line 626 (`response_text = strip_hallucinated_turns(response_text)`) with:
```python
    if not request.raw_passthrough:
        response_text = strip_hallucinated_turns(response_text)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `./venv/bin/python -m pytest tests/test_openai_compat.py -q`
Expected: PASS (all route tests, including the 3 new ones — and the pre-existing strip tests still pass).

- [ ] **Step 6: Commit**

```bash
git add app/routes/openai_compat.py tests/test_openai_compat.py
git commit -m "feat(openai-compat): honor raw_passthrough (skip relabel + skip strip)"
```

---

## GROUP B — Vendor the fork & set up config
*(Repo: `/Users/mkrolick/Documents/GitHub/SmallDesire`.)*

### Task 4: Vendor the upstream backend subset

**Files:**
- Create: `generative_agents/` (subset of upstream at the pinned commit)
- Create: `.gitignore`

- [ ] **Step 1: Clone upstream at the pinned commit and copy the subset**

```bash
cd /Users/mkrolick/Documents/GitHub/SmallDesire
rm -rf /tmp/ga-src && git clone https://github.com/joonspk-research/generative_agents /tmp/ga-src
git -C /tmp/ga-src checkout fe05a71d3e4ed7d10bf68aa4eda6dd995ec070f4
mkdir -p generative_agents/environment/frontend_server/static_dirs/assets
mkdir -p generative_agents/environment/frontend_server/storage
mkdir -p generative_agents/environment/frontend_server/temp_storage
cp -R /tmp/ga-src/reverie generative_agents/reverie
cp -R "/tmp/ga-src/environment/frontend_server/static_dirs/assets/the_ville" generative_agents/environment/frontend_server/static_dirs/assets/the_ville
cp -R "/tmp/ga-src/environment/frontend_server/storage/base_the_ville_isabella_maria_klaus" generative_agents/environment/frontend_server/storage/
cp /tmp/ga-src/requirements.txt generative_agents/requirements-upstream.txt
cp /tmp/ga-src/LICENSE generative_agents/LICENSE
```

- [ ] **Step 2: Write `.gitignore`**

Create `/Users/mkrolick/Documents/GitHub/SmallDesire/.gitignore`:
```gitignore
# Python
__pycache__/
*.pyc
.venv/
venv/
.env

# Per-run sim outputs (keep only base_* sims under version control)
generative_agents/environment/frontend_server/storage/*
!generative_agents/environment/frontend_server/storage/base_*

# Backend writes signaling files here at runtime
generative_agents/environment/frontend_server/temp_storage/*.json
```

- [ ] **Step 3: Verify the subset is present and laid out correctly**

Run:
```bash
ls generative_agents/reverie/backend_server/reverie.py \
   generative_agents/reverie/backend_server/persona/prompt_template/gpt_structure.py \
   generative_agents/environment/frontend_server/static_dirs/assets/the_ville/matrix \
   "generative_agents/environment/frontend_server/storage/base_the_ville_isabella_maria_klaus/reverie/meta.json"
```
Expected: all four paths print (no "No such file"). The `matrix` line lists a directory.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore: vendor generative_agents backend subset (pinned fe05a71)"
```

### Task 5: Create the Python environment

**Files:** none (environment only)

- [ ] **Step 1: Create the venv and install the minimal deps**

```bash
cd /Users/mkrolick/Documents/GitHub/SmallDesire
python3 -m venv .venv
./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install "numpy<2" requests pytest
```
(We deliberately do **not** install `requirements-upstream.txt` — the headless backend path only needs `numpy`; `requests` is for the provider client; `pytest` for tests.)

- [ ] **Step 2: Verify numpy imports under the venv**

Run: `./.venv/bin/python -c "import numpy, requests, pytest; print('deps ok')"`
Expected: prints `deps ok`.

- [ ] **Step 3: Commit** (records the chosen deps; nothing to add if `.venv` is gitignored — instead pin them)

Create `generative_agents/requirements.txt`:
```text
numpy<2
requests
pytest
```
```bash
git add generative_agents/requirements.txt
git commit -m "chore: pin minimal headless deps (numpy, requests, pytest)"
```

### Task 6: Create `utils.py` (config + provider env vars)

**Files:**
- Create: `generative_agents/reverie/backend_server/utils.py`

- [ ] **Step 1: Write `utils.py`**

Create `generative_agents/reverie/backend_server/utils.py`:
```python
import os

# --- Legacy config (paths are relative to reverie/backend_server) ---
openai_api_key = "unused"          # legacy global; kept so imports don't break
key_owner = "SmallDesire"
maze_assets_loc = "../../environment/frontend_server/static_dirs/assets"
env_matrix = f"{maze_assets_loc}/the_ville/matrix"
env_visuals = f"{maze_assets_loc}/the_ville/visuals"
fs_storage = "../../environment/frontend_server/storage"
fs_temp_storage = "../../environment/frontend_server/temp_storage"
collision_block_id = "32125"
debug = True

# --- SmallDesire provider config (read from env; safe local defaults) ---
TOKENSPLS_BASE_URL = os.environ.get("TOKENSPLS_BASE_URL", "http://127.0.0.1:8000/v1")
TOKENSPLS_MODEL = os.environ.get("TOKENSPLS_MODEL", "gpt-5.4")
TOKENSPLS_API_KEY = os.environ.get("TOKENSPLS_API_KEY", "sk-noauth")
EMBED_BASE_URL = os.environ.get("EMBED_BASE_URL", "https://api.openai.com/v1")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "text-embedding-3-small")
EMBED_API_KEY = os.environ.get("EMBED_API_KEY", "")
```

- [ ] **Step 2: Verify it imports from the correct CWD**

Run: `cd generative_agents/reverie/backend_server && ../../../.venv/bin/python -c "from utils import fs_storage, TOKENSPLS_MODEL; print(fs_storage, TOKENSPLS_MODEL)"`
Expected: prints `../../environment/frontend_server/storage gpt-5.4`.

- [ ] **Step 3: Commit**

```bash
cd /Users/mkrolick/Documents/GitHub/SmallDesire
git add -f generative_agents/reverie/backend_server/utils.py
git commit -m "feat: add utils.py with provider config (env-backed)"
```
(`-f` because upstream `.gitignore` inside the vendored tree ignores this file.)

---

## GROUP C — Provider-agnostic LLM client

### Task 7: Create `provider_client.py`

**Files:**
- Create: `generative_agents/reverie/backend_server/persona/prompt_template/provider_client.py`
- Create: `generative_agents/reverie/backend_server/conftest.py` (empty — anchors pytest rootdir at backend_server)
- Test: `generative_agents/reverie/backend_server/tests/test_provider_client.py`

*(All test commands in Groups C/D run from `generative_agents/reverie/backend_server/`. Define `PY=../../../.venv/bin/python` mentally.)*

- [ ] **Step 1: Write the failing tests**

Create `generative_agents/reverie/backend_server/conftest.py` as an empty file, then create `tests/test_provider_client.py`:
```python
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
    assert pc._post_with_retry("http://x", {}, {}, repeat=3) == {"ok": True}
    assert calls["n"] == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd generative_agents/reverie/backend_server && ../../../.venv/bin/python -m pytest tests/test_provider_client.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'persona.prompt_template.provider_client'`.

- [ ] **Step 3: Implement `provider_client.py`**

Create `generative_agents/reverie/backend_server/persona/prompt_template/provider_client.py`:
```python
"""provider_client.py — provider-agnostic LLM access for the SmallDesire fork.

Chat/generation -> TokensPLS (OpenAI-compatible proxy); embeddings -> a separate
external provider. Drop-in replacement for the legacy openai==0.27 calls.
No global SDK state; config comes from utils.py (env-backed).
"""
import time
import requests

from utils import (
    TOKENSPLS_BASE_URL, TOKENSPLS_MODEL, TOKENSPLS_API_KEY,
    EMBED_BASE_URL, EMBED_MODEL, EMBED_API_KEY,
)

_TIMEOUT = 120


def _post_with_retry(url, payload, headers, repeat=3):
    """POST JSON with exponential backoff on transient faults. Raises on exhaustion."""
    last_exc = None
    for i in range(repeat):
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=_TIMEOUT)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 429 or r.status_code >= 500:
                last_exc = RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
            else:
                r.raise_for_status()
                return r.json()
        except requests.RequestException as e:
            last_exc = e
        time.sleep(0.5 * (2 ** i))
    raise last_exc if last_exc else RuntimeError("request failed")


def chat_completion(prompt, max_tokens=None, temperature=None, stop=None):
    """Single-prompt chat via TokensPLS. Returns the assistant message content (str)."""
    payload = {
        "model": TOKENSPLS_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "raw_passthrough": True,
    }
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if temperature is not None:
        payload["temperature"] = temperature
    if stop is not None:
        payload["stop"] = stop
    headers = {"Authorization": f"Bearer {TOKENSPLS_API_KEY}", "Content-Type": "application/json"}
    resp = _post_with_retry(f"{TOKENSPLS_BASE_URL}/chat/completions", payload, headers)
    return resp["choices"][0]["message"]["content"]


def get_embedding(text):
    """Embed a single string via the external provider. Returns a bare list[float]."""
    payload = {"input": [text], "model": EMBED_MODEL}
    headers = {"Authorization": f"Bearer {EMBED_API_KEY}", "Content-Type": "application/json"}
    resp = _post_with_retry(f"{EMBED_BASE_URL}/embeddings", payload, headers)
    return resp["data"][0]["embedding"]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd generative_agents/reverie/backend_server && ../../../.venv/bin/python -m pytest tests/test_provider_client.py -q`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
cd /Users/mkrolick/Documents/GitHub/SmallDesire
git add -f generative_agents/reverie/backend_server/persona/prompt_template/provider_client.py
git add generative_agents/reverie/backend_server/conftest.py generative_agents/reverie/backend_server/tests/test_provider_client.py
git commit -m "feat: provider-agnostic LLM client (chat->TokensPLS, embed->external)"
```

### Task 8: Wire `gpt_structure.py` to `provider_client`

**Files:**
- Modify: `generative_agents/reverie/backend_server/persona/prompt_template/gpt_structure.py` (lines 11–14 header; `ChatGPT_single_request`, `GPT4_request`, `ChatGPT_request`, `GPT_request`, `get_embedding`)
- Test: `generative_agents/reverie/backend_server/tests/test_gpt_structure_contract.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_gpt_structure_contract.py`:
```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd generative_agents/reverie/backend_server && ../../../.venv/bin/python -m pytest tests/test_gpt_structure_contract.py -q`
Expected: FAIL — `AttributeError: module ... gpt_structure has no attribute 'provider_client'` (it still imports `openai`).

- [ ] **Step 3: Replace the header imports**

In `gpt_structure.py`, replace lines 11–14:
```python
import openai
import time 

from utils import *

openai.api_key = openai_api_key
```
with:
```python
import time

from utils import *
from persona.prompt_template import provider_client
```

- [ ] **Step 4: Replace the five call sites**

Replace `ChatGPT_single_request` with:
```python
def ChatGPT_single_request(prompt):
  temp_sleep()
  return provider_client.chat_completion(prompt)
```
Replace `GPT4_request` with:
```python
def GPT4_request(prompt):
  temp_sleep()
  try:
    return provider_client.chat_completion(prompt)
  except:
    print("ChatGPT ERROR")
    return "ChatGPT ERROR"
```
Replace `ChatGPT_request` with:
```python
def ChatGPT_request(prompt):
  try:
    return provider_client.chat_completion(prompt)
  except:
    print("ChatGPT ERROR")
    return "ChatGPT ERROR"
```
Replace `GPT_request` with:
```python
def GPT_request(prompt, gpt_parameter):
  temp_sleep()
  try:
    return provider_client.chat_completion(
        prompt,
        max_tokens=gpt_parameter.get("max_tokens"),
        temperature=gpt_parameter.get("temperature"),
        stop=gpt_parameter.get("stop"))
  except:
    print("TOKEN LIMIT EXCEEDED")
    return "TOKEN LIMIT EXCEEDED"
```
Replace `get_embedding` with:
```python
def get_embedding(text, model="text-embedding-3-small"):
  text = text.replace("\n", " ")
  if not text:
    text = "this is blank"
  return provider_client.get_embedding(text)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd generative_agents/reverie/backend_server && ../../../.venv/bin/python -m pytest tests/test_gpt_structure_contract.py -q`
Expected: PASS (4 passed).

- [ ] **Step 6: Commit**

```bash
cd /Users/mkrolick/Documents/GitHub/SmallDesire
git add -f generative_agents/reverie/backend_server/persona/prompt_template/gpt_structure.py
git add generative_agents/reverie/backend_server/tests/test_gpt_structure_contract.py
git commit -m "refactor: route gpt_structure LLM calls through provider_client"
```

---

## GROUP D — Headless runtime

### Task 9: Create the 2-agent base sim

**Files:**
- Create: `generative_agents/environment/frontend_server/storage/base_the_ville_isabella_maria/` (from the 3-agent base)
- Test: `generative_agents/reverie/backend_server/tests/test_two_agent_base.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_two_agent_base.py`:
```python
import json
import os

BASE = "../../environment/frontend_server/storage/base_the_ville_isabella_maria"
EXPECTED = {"Isabella Rodriguez", "Maria Lopez"}


def test_two_agent_base_is_consistent():
    meta = json.load(open(f"{BASE}/reverie/meta.json"))
    names = set(meta["persona_names"])
    env = json.load(open(f"{BASE}/environment/0.json"))
    dirs = {d for d in os.listdir(f"{BASE}/personas") if not d.startswith(".")}
    assert names == EXPECTED
    assert set(env.keys()) == EXPECTED
    assert dirs == EXPECTED
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd generative_agents/reverie/backend_server && ../../../.venv/bin/python -m pytest tests/test_two_agent_base.py -q`
Expected: FAIL — `FileNotFoundError` (the base directory doesn't exist yet).

- [ ] **Step 3: Create and trim the base**

```bash
cd /Users/mkrolick/Documents/GitHub/SmallDesire/generative_agents/environment/frontend_server/storage
cp -R base_the_ville_isabella_maria_klaus base_the_ville_isabella_maria
rm -rf "base_the_ville_isabella_maria/personas/Klaus Mueller"
```
Then edit `base_the_ville_isabella_maria/reverie/meta.json`: remove `"Klaus Mueller"` from the `persona_names` array (leave it `["Isabella Rodriguez", "Maria Lopez"]`; keep every other field unchanged).
Then edit `base_the_ville_isabella_maria/environment/0.json`: delete the entire `"Klaus Mueller": {...}` entry (keep Isabella and Maria).

- [ ] **Step 4: Run test to verify it passes**

Run: `cd generative_agents/reverie/backend_server && ../../../.venv/bin/python -m pytest tests/test_two_agent_base.py -q`
Expected: PASS (1 passed).

- [ ] **Step 5: Commit**

```bash
cd /Users/mkrolick/Documents/GitHub/SmallDesire
git add -A
git commit -m "feat: add 2-agent base sim (Isabella + Maria)"
```

### Task 10: Add `process_step()` to `ReverieServer`

**Files:**
- Modify: `generative_agents/reverie/backend_server/reverie.py` (line 31 dead import; `__init__` ~line 133; new method)
- Test: `generative_agents/reverie/backend_server/tests/test_process_step.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_process_step.py`:
```python
import datetime
import json
import shutil

import reverie
from utils import fs_storage

NAMES = {"Isabella Rodriguez", "Maria Lopez"}


def test_process_step_writes_movement_and_advances(monkeypatch):
    sim = "test_process_step_unit"
    folder = f"{fs_storage}/{sim}"
    shutil.rmtree(folder, ignore_errors=True)
    rs = reverie.ReverieServer("base_the_ville_isabella_maria", sim)
    for p in rs.personas.values():
        monkeypatch.setattr(p, "move", lambda maze, personas, tile, t: ((1, 2), "S", "idle @ home"))
    env = json.load(open(f"{folder}/environment/0.json"))
    t0 = rs.curr_time
    movements = rs.process_step(env)
    assert set(movements["persona"].keys()) == NAMES
    saved = json.load(open(f"{folder}/movement/0.json"))
    assert saved["persona"]["Isabella Rodriguez"]["movement"] == [1, 2]
    assert saved["meta"]["curr_time"] == t0.strftime("%B %d, %Y, %H:%M:%S")
    assert rs.curr_time == t0 + datetime.timedelta(seconds=rs.sec_per_step)
    shutil.rmtree(folder, ignore_errors=True)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd generative_agents/reverie/backend_server && ../../../.venv/bin/python -m pytest tests/test_process_step.py -q`
Expected: FAIL — `AttributeError: 'ReverieServer' object has no attribute 'process_step'` (or an `ImportError` on `selenium` if it isn't installed — fixed in Step 3).

- [ ] **Step 3: Remove the dead `selenium` import**

In `reverie.py`, delete line 31: `from selenium import webdriver`.

- [ ] **Step 4: Initialize the cleanup state**

In `reverie.py` `ReverieServer.__init__`, immediately after the persona-loading loop (right before the `# REVERIE SETTINGS PARAMETERS` / `self.server_sleep = 0.1` area, ~line 133), add:
```python
    # Headless: game-object cleanup state carried across process_step calls.
    self._game_obj_cleanup = dict()
```

- [ ] **Step 5: Add the `process_step` method**

Add this method to the `ReverieServer` class (e.g., directly above `start_server`):
```python
  def process_step(self, new_env):
    """Headless single step. `new_env` is {name: {"x":int,"y":int}} (the dict the
    frontend would have written). Advances one tick, writes movement/<step>.json,
    returns the movements dict. Body lifted verbatim from start_server's loop."""
    sim_folder = f"{fs_storage}/{self.sim_code}"

    for key, val in self._game_obj_cleanup.items():
      self.maze.turn_event_from_tile_idle(key, val)
    self._game_obj_cleanup = dict()

    for persona_name, persona in self.personas.items():
      curr_tile = self.personas_tile[persona_name]
      new_tile = (new_env[persona_name]["x"], new_env[persona_name]["y"])
      self.personas_tile[persona_name] = new_tile
      self.maze.remove_subject_events_from_tile(persona.name, curr_tile)
      self.maze.add_event_from_tile(persona.scratch.get_curr_event_and_desc(), new_tile)
      if not persona.scratch.planned_path:
        self._game_obj_cleanup[persona.scratch.get_curr_obj_event_and_desc()] = new_tile
        self.maze.add_event_from_tile(persona.scratch.get_curr_obj_event_and_desc(), new_tile)
        blank = (persona.scratch.get_curr_obj_event_and_desc()[0], None, None, None)
        self.maze.remove_event_from_tile(blank, new_tile)

    movements = {"persona": dict(), "meta": dict()}
    for persona_name, persona in self.personas.items():
      next_tile, pronunciatio, description = persona.move(
          self.maze, self.personas, self.personas_tile[persona_name], self.curr_time)
      movements["persona"][persona_name] = {
          "movement": next_tile,
          "pronunciatio": pronunciatio,
          "description": description,
          "chat": persona.scratch.chat,
      }
    movements["meta"]["curr_time"] = self.curr_time.strftime("%B %d, %Y, %H:%M:%S")

    os.makedirs(f"{sim_folder}/movement", exist_ok=True)
    with open(f"{sim_folder}/movement/{self.step}.json", "w") as outfile:
      outfile.write(json.dumps(movements, indent=2))

    self.step += 1
    self.curr_time += datetime.timedelta(seconds=self.sec_per_step)
    return movements
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd generative_agents/reverie/backend_server && ../../../.venv/bin/python -m pytest tests/test_process_step.py -q`
Expected: PASS (1 passed). (No network — `persona.move` is stubbed.)

- [ ] **Step 7: Commit**

```bash
cd /Users/mkrolick/Documents/GitHub/SmallDesire
git add -f generative_agents/reverie/backend_server/reverie.py
git add generative_agents/reverie/backend_server/tests/test_process_step.py
git commit -m "feat: add ReverieServer.process_step for headless stepping"
```

### Task 11: Create the headless driver + feeder

**Files:**
- Create: `generative_agents/reverie/backend_server/headless.py`
- Test: `generative_agents/reverie/backend_server/tests/test_feeder.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_feeder.py`:
```python
import headless


def test_next_env_from_movements_echoes_tiles():
    mv = {"persona": {"A": {"movement": [5, 6]}, "B": {"movement": [7, 8]}}, "meta": {}}
    env = headless.next_env_from_movements(mv)
    assert env == {
        "A": {"maze": "the_ville", "x": 5, "y": 6},
        "B": {"maze": "the_ville", "x": 7, "y": 8},
    }
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd generative_agents/reverie/backend_server && ../../../.venv/bin/python -m pytest tests/test_feeder.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'headless'`.

- [ ] **Step 3: Implement `headless.py`**

Create `generative_agents/reverie/backend_server/headless.py`:
```python
"""Headless driver for a forked 2-agent sim — no Phaser frontend, no disk polling.

The Phaser frontend's only contribution each step is to echo the backend's
movement tile back as the next environment (sprite lands exactly on the tile),
so `next_env_from_movements` reproduces that handshake in-process.
"""
import json
import sys

from reverie import ReverieServer
from utils import fs_storage


def next_env_from_movements(movements):
    """The feeder: next environment = each persona's just-written movement tile."""
    env = {}
    for name, m in movements["persona"].items():
        x, y = m["movement"]
        env[name] = {"maze": "the_ville", "x": x, "y": y}
    return env


def run_headless(fork_sim_code, sim_code, n_steps):
    """Fork `fork_sim_code` into `sim_code`, run `n_steps`, save. Returns the server."""
    rs = ReverieServer(fork_sim_code, sim_code)
    sim_folder = f"{fs_storage}/{sim_code}"
    with open(f"{sim_folder}/environment/{rs.step}.json") as f:
        env = json.load(f)
    for _ in range(n_steps):
        movements = rs.process_step(env)
        env = next_env_from_movements(movements)
    rs.save()
    return rs


if __name__ == "__main__":
    run_headless(sys.argv[1], sys.argv[2], int(sys.argv[3]))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd generative_agents/reverie/backend_server && ../../../.venv/bin/python -m pytest tests/test_feeder.py -q`
Expected: PASS (1 passed).

- [ ] **Step 5: Commit**

```bash
cd /Users/mkrolick/Documents/GitHub/SmallDesire
git add -f generative_agents/reverie/backend_server/headless.py
git add generative_agents/reverie/backend_server/tests/test_feeder.py
git commit -m "feat: headless driver + in-process environment feeder"
```

### Task 12: End-to-end smoke (one real step)

**Files:**
- Test: `generative_agents/reverie/backend_server/tests/test_smoke_integration.py`

*(This is the **integration** gate: it makes real LLM + embedding calls. It is skipped unless `RUN_INTEGRATION=1`. Expect it to take a few minutes for the first step — the agents generate a full day plan — and it may surface the 30K-char TokensPLS cap on the largest prompts; both are expected Phase-0 signal, see the spec's risk table.)*

- [ ] **Step 1: Write the smoke test**

Create `tests/test_smoke_integration.py`:
```python
import json
import os
import shutil

import pytest

import headless
from utils import fs_storage

NAMES = ["Isabella Rodriguez", "Maria Lopez"]


@pytest.mark.skipif(not os.environ.get("RUN_INTEGRATION"),
                    reason="set RUN_INTEGRATION=1 with TokensPLS up + EMBED_API_KEY set")
def test_one_real_step_end_to_end():
    sim = "smoke_2agent"
    folder = f"{fs_storage}/{sim}"
    shutil.rmtree(folder, ignore_errors=True)
    headless.run_headless("base_the_ville_isabella_maria", sim, 1)
    mv = json.load(open(f"{folder}/movement/0.json"))
    for name in NAMES:
        assert name in mv["persona"]
        assert len(mv["persona"][name]["movement"]) == 2
        assert all(isinstance(c, int) for c in mv["persona"][name]["movement"])
    assert mv["meta"]["curr_time"] == "February 13, 2023, 00:00:10"
    shutil.rmtree(folder, ignore_errors=True)
```

- [ ] **Step 2: Start TokensPLS and export credentials**

In a separate shell: `cd /Users/mkrolick/Code/TokensPLS && make start-all` (brings up the proxy on `http://127.0.0.1:8000`). Then, in the test shell:
```bash
export RUN_INTEGRATION=1
export TOKENSPLS_BASE_URL=http://127.0.0.1:8000/v1
export TOKENSPLS_MODEL=gpt-5.4
export EMBED_BASE_URL=https://api.openai.com/v1
export EMBED_MODEL=text-embedding-3-small
export EMBED_API_KEY=sk-...   # a real embeddings key
```

- [ ] **Step 3: Run the smoke**

Run: `cd generative_agents/reverie/backend_server && ../../../.venv/bin/python -m pytest tests/test_smoke_integration.py -v -s`
Expected: PASS (1 passed). `movement/0.json` contains both personas with integer 2-tuples and `curr_time` advanced by 10 seconds — proving env-read → `persona.move` (perceive→retrieve→plan→reflect→execute, with real TokensPLS chat + external embeddings) → movement-write all fired end-to-end.

- [ ] **Step 4: Run the full offline suite once to confirm green**

Run: `cd generative_agents/reverie/backend_server && ../../../.venv/bin/python -m pytest tests/ -q -k "not Integration and not integration"` and (from `/Users/mkrolick/Code/TokensPLS`) `make test`.
Expected: all offline SmallDesire tests pass; TokensPLS suite passes.

- [ ] **Step 5: Commit**

```bash
cd /Users/mkrolick/Documents/GitHub/SmallDesire
git add generative_agents/reverie/backend_server/tests/test_smoke_integration.py
git commit -m "test: end-to-end headless 2-agent smoke (integration-gated)"
```

---

## Self-Review

**Spec coverage (Phase 0 of the design spec §6.2):**
1. Fork `generative_agents`; pin env → **Tasks 4, 5.**
2. Provider-agnostic client; chat→TokensPLS/`gpt-5.4`, embeddings→external → **Tasks 6, 7, 8.**
3. Run backend headless for a 2-agent scenario → **Tasks 9, 10, 11, 12.**
4. TokensPLS raw-passthrough mode + context headroom → **Group A (Tasks 1–3)**; context-cap headroom is *surfaced* (not solved) by Task 12 and documented as expected Phase-0 signal (spec risk #2) — solving it (retrieval-count capping) is deferred to the instrumentation plan where prompt sizes are tuned.
5. Instrumentation hooks, persona/perturbation pipeline, conflict affordances, measurement layer → **deferred to Roadmap plans** (out of this plan's scope by design).

**Placeholder scan:** none — every code step shows complete code; every run step shows the command and expected output.

**Type/name consistency:** `provider_client.chat_completion` / `get_embedding` / `_post_with_retry` are defined in Task 7 and used identically in Tasks 8/12; `process_step(new_env)` defined in Task 10 and called in Task 11; `next_env_from_movements` defined and tested with the same signature; the 2-agent base name `base_the_ville_isabella_maria` is identical across Tasks 9–12.

---

## Roadmap (subsequent plans — each its own spec→plan cycle)

2. **Instrumentation & logging** — per-tick capture of `generate_summarize_agent_relationship`, reflection/thought nodes keyed to the partner, transcripts, and post-convo memos to structured logs; decide retrieval-count caps for the 30K char limit.
3. **Persona generation & perturbation pipeline** — trait-vector → symmetric δ-perturbation → length-matched ISS render into `scratch.json`, with the three manipulation-check distance metrics.
4. **Conflict affordances (maximal)** — gossip / exclude / sabotage / recruit-against + public reputation, as world actions.
5. **Measurement layer & Phase-1 runner** — private-reflection probe + isolation audit, blind cross-family judge panel, the four doubling-signature computations, sycophancy baseline; then the 1-high/1-low existence probe.

---

## Execution Handoff

(filled in by the assistant after you approve the plan)
