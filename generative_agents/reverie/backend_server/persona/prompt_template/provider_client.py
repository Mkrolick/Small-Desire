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


def _post_with_retry(url, payload, headers, max_attempts=3):
    """POST JSON with exponential backoff on TRANSIENT faults (429 / 5xx / network
    errors). Non-retryable responses (other 4xx) fail fast. Raises on exhaustion."""
    last_exc = None
    for i in range(max_attempts):
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=_TIMEOUT)
        except requests.RequestException as e:
            last_exc = e
        else:
            if r.status_code == 200:
                return r.json()
            if r.status_code == 429 or r.status_code >= 500:
                last_exc = RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
            else:
                raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
        if i < max_attempts - 1:
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
