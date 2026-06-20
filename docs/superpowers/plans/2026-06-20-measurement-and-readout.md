# Measurement & Readout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Measure the dependent variable — each agent's felt attitude toward the other — by simply *asking the agent via an LLM call* ("on a 1–7 scale, how warm vs. hostile do you feel toward X, and why"), logged per step; then read the four doubling signatures off those score trajectories with simple trend math.

**Architecture:** A scaled self-report **`probe_feelings`** added to `instrumentation.py` (a more pointed sibling of the existing `probe_relationships`): per ordered pair, it retrieves what A knows about B, asks A — *in character* — for a 1–7 warmth↔hostility score + reason via `provider_client.chat_completion` (→ TokensPLS), parses it robustly (gpt-5.4-safe), and logs a `feeling` record. It's wired into `run_headless_instrumented`. A separate **`signatures.py`** reads the `feeling.jsonl` trajectories offline (no LLM) and computes escalation slope, A↔B reciprocity, and convergence — plain `numpy`. (A blind LLM-judge over transcripts is an optional later add-on, intentionally out of scope here per the simplified design.)

**Tech Stack:** Python 3.13, `numpy`, `re`, `provider_client` (→ TokensPLS). pytest; live path gated.

---

## Context (grounded — verified on `main`)

- `instrumentation.py` already has `MeasurementLog.record(kind, step, curr_time, payload)`, `probe_relationships(personas, log, step, curr_time, n_retrieve=50)`, and imports `from persona.cognitive_modules import converse` + `from persona.cognitive_modules.retrieve import new_retrieve`. ConceptNode has `.embedding_key`.
- `provider_client.chat_completion(prompt, ...)` returns a str (routes to TokensPLS with `raw_passthrough`).
- `persona.scratch` exposes `get_str_iss()` (the Identity Stable Set / persona block) on real personas; tests use fakes without it, so access it defensively.
- `run_headless_instrumented(fork, sim, n_steps, probe_every)` calls the per-step captures + `probe_relationships`.
- Commands run from `generative_agents/reverie/backend_server/`; `PY=../../../.venv/bin/python`.

---

## File Structure

| Path | Responsibility |
|---|---|
| `generative_agents/reverie/backend_server/instrumentation.py` | **Modify.** Add `_parse_feeling` + `probe_feelings`; call it from... (wiring is Task 2). |
| `generative_agents/reverie/backend_server/headless.py` | **Modify.** Call `probe_feelings` each probe step in `run_headless_instrumented`. |
| `generative_agents/reverie/backend_server/signatures.py` | **Create.** `load_feelings`, `escalation_slope`, `reciprocity`, `convergence`, `compute_signatures`. |
| `generative_agents/reverie/backend_server/tests/test_feelings.py` | **Create.** Probe tests (offline, mocked LLM). |
| `generative_agents/reverie/backend_server/tests/test_signatures.py` | **Create.** Readout tests (synthetic trajectories). |
| `generative_agents/reverie/backend_server/tests/test_feelings_integration.py` | **Create.** Gated live probe check. |

---

### Task 1: `probe_feelings` — the scaled self-report probe

**Files:**
- Modify: `instrumentation.py`
- Test: `tests/test_feelings.py`

- [ ] **Step 1: Write the failing test** — create `tests/test_feelings.py`:
```python
import types

import instrumentation as instr


def _fake_persona(name):
    scratch = types.SimpleNamespace(name=name)  # no get_str_iss -> defensive access yields ""
    return types.SimpleNamespace(scratch=scratch)


def test_parse_feeling_structured_and_fallback():
    assert instr._parse_feeling("SCORE: 6 | REASON: she keeps copying me") == (6, "she keeps copying me")
    # fallback: no SCORE label, but a lone digit + prose
    score, reason = instr._parse_feeling("I'd say a 5 because it's tense")
    assert score == 5 and "tense" in reason
    # scale echo must not be mistaken for the answer
    s2, _ = instr._parse_feeling("On a 1 to 7 scale, SCORE: 7 | REASON: hostile")
    assert s2 == 7
    assert instr._parse_feeling("no number here")[0] is None


def test_probe_feelings_logs_both_directions(monkeypatch):
    sim = "test_feelings_unit"
    log = instr.MeasurementLog(sim)
    monkeypatch.setattr(instr, "new_retrieve", lambda persona, fp, n_count=30: {fp[0]: []})
    calls = []
    def fake_chat(prompt, **kw):
        calls.append(prompt)
        return "SCORE: 4 | REASON: wary of them"
    monkeypatch.setattr(instr.provider_client, "chat_completion", fake_chat)

    personas = {"Ada Rivera": _fake_persona("Ada Rivera"), "Bea Rivera": _fake_persona("Bea Rivera")}
    instr.probe_feelings(personas, log, step=3, curr_time=__import__("datetime").datetime(2023, 2, 13, 0, 5, 0))

    path = f"{instr.fs_storage}/{sim}/measurements/feeling.jsonl"
    lines = [__import__("json").loads(l) for l in open(path)]
    assert len(lines) == 2
    assert {(l["from"], l["to"]) for l in lines} == {("Ada Rivera", "Bea Rivera"), ("Bea Rivera", "Ada Rivera")}
    assert all(l["score"] == 4 and "wary" in l["reason"] for l in lines)
    # the prompt names both the speaker and the target (asked in character)
    assert any("Ada Rivera" in p and "Bea Rivera" in p for p in calls)
    import shutil
    shutil.rmtree(f"{instr.fs_storage}/{sim}", ignore_errors=True)
```

- [ ] **Step 2: Run to verify it fails** — `$PY -m pytest tests/test_feelings.py -q` → FAIL (`AttributeError: module 'instrumentation' has no attribute '_parse_feeling'`).

- [ ] **Step 3: Implement** — add to `instrumentation.py`. First add imports at the top (below the existing imports):
```python
import re

from persona.prompt_template import provider_client
```
Then add:
```python
def _persona_iss(persona):
    """The persona's identity block if available (real personas have get_str_iss)."""
    getter = getattr(persona.scratch, "get_str_iss", None)
    return getter() if callable(getter) else ""


def _parse_feeling(text):
    """Extract a 1-7 score and reason from a feeling response (gpt-5.4-safe).
    Prefers the explicit 'SCORE: n | REASON: ...' format; falls back to the first
    standalone 1-7 digit. Returns (score|None, reason)."""
    m = re.search(r"SCORE:\s*([1-7])", text, re.IGNORECASE)
    if not m:
        m = re.search(r"\b([1-7])\b", text)
    score = int(m.group(1)) if m else None
    rm = re.search(r"REASON:\s*(.+)", text, re.IGNORECASE | re.DOTALL)
    reason = (rm.group(1) if rm else text).strip()
    return score, reason


def probe_feelings(personas, log, step, curr_time, n_retrieve=30):
    """Ask each agent, in character, how warm vs. hostile it feels toward the other
    (1=warm .. 7=hostile) + why, via an LLM call. Logs a 'feeling' record per
    ordered pair. This is the primary DV: the agent's self-reported attitude."""
    names = list(personas.keys())
    for a_name in names:
        for b_name in names:
            if a_name == b_name:
                continue
            a, b = personas[a_name], personas[b_name]
            retrieved = new_retrieve(a, [b.scratch.name], n_retrieve)
            context = "\n".join(node.embedding_key for nodes in retrieved.values() for node in nodes)
            prompt = (
                f"You are {a.scratch.name}. {_persona_iss(a)}\n"
                f"Here is what you know and remember about {b.scratch.name}:\n{context}\n\n"
                f"On a scale of 1 to 7, where 1 means warm and friendly and 7 means hostile "
                f"and resentful, how do you genuinely feel about {b.scratch.name} right now?\n"
                f"Respond in exactly this format and nothing else:\n"
                f"SCORE: <a single number 1-7> | REASON: <one short sentence>"
            )
            resp = provider_client.chat_completion(prompt)
            score, reason = _parse_feeling(resp)
            log.record("feeling", step, curr_time, {
                "from": a_name, "to": b_name, "score": score, "reason": reason, "raw": resp,
            })
```

- [ ] **Step 4: Run to verify it passes** — `$PY -m pytest tests/test_feelings.py -q` → PASS (2 passed). Confirm import: `$PY -c "import instrumentation; print('ok')"`.

- [ ] **Step 5: Commit**
```bash
cd /Users/mkrolick/Documents/GitHub/SmallDesire
git add -f generative_agents/reverie/backend_server/instrumentation.py
git add generative_agents/reverie/backend_server/tests/test_feelings.py
git commit -m "feat: scaled self-report feeling probe (the DV, via LLM)"
```

---

### Task 2: Wire `probe_feelings` into the instrumented runner

**Files:**
- Modify: `headless.py`
- Test: `tests/test_feelings.py`

- [ ] **Step 1: Write the failing test** — APPEND to `tests/test_feelings.py`:
```python
def test_run_headless_instrumented_writes_feelings(monkeypatch):
    import shutil
    import reverie
    import headless
    sim = "test_feelings_run"
    folder = f"{instr.fs_storage}/{sim}"
    shutil.rmtree(folder, ignore_errors=True)

    monkeypatch.setattr(instr, "new_retrieve", lambda persona, fp, n_count=30: {fp[0]: []})
    monkeypatch.setattr(instr.converse, "generate_summarize_agent_relationship",
                        lambda a, b, retrieved: "summary")
    monkeypatch.setattr(instr.provider_client, "chat_completion",
                        lambda prompt, **kw: "SCORE: 5 | REASON: tense")
    monkeypatch.setattr(reverie.ReverieServer, "save", lambda self: None)
    orig_init = reverie.ReverieServer.__init__
    def patched_init(self, fork, sim_code):
        orig_init(self, fork, sim_code)
        for p in self.personas.values():
            monkeypatch.setattr(p, "move", lambda maze, personas, tile, t: ((1, 2), "S", "idle @ home"))
    monkeypatch.setattr(reverie.ReverieServer, "__init__", patched_init)

    headless.run_headless_instrumented("base_the_ville_isabella_maria", sim, 2, probe_every=1)
    feelings = [__import__("json").loads(l) for l in open(f"{folder}/measurements/feeling.jsonl")]
    assert len(feelings) == 4   # 2 ordered pairs x 2 steps
    assert all(f["score"] == 5 for f in feelings)
    shutil.rmtree(folder, ignore_errors=True)
```

- [ ] **Step 2: Run to verify it fails** — `$PY -m pytest tests/test_feelings.py -k run_headless_instrumented -q` → FAIL (no `feeling.jsonl` written — `probe_feelings` not wired in).

- [ ] **Step 3: Implement** — in `headless.py` `run_headless_instrumented`, in the probe block, add the feelings probe right after the relationship probe:
```python
        if probe_every and (i % probe_every == 0):
            instrumentation.probe_relationships(rs.personas, log, step, step_time)
            instrumentation.probe_feelings(rs.personas, log, step, step_time)
```

- [ ] **Step 4: Run to verify it passes** — `$PY -m pytest tests/test_feelings.py -q` → PASS. Then full suite `$PY -m pytest tests/ -q` → all pass + (now 5) skipped.

- [ ] **Step 5: Commit**
```bash
cd /Users/mkrolick/Documents/GitHub/SmallDesire
git add -f generative_agents/reverie/backend_server/headless.py
git add generative_agents/reverie/backend_server/tests/test_feelings.py
git commit -m "feat: capture the feeling probe each step in run_headless_instrumented"
```

---

### Task 3: `signatures.py` — read the doubling signatures off the trajectories

**Files:**
- Create: `signatures.py`
- Test: `tests/test_signatures.py`

- [ ] **Step 1: Write the failing test** — create `tests/test_signatures.py`:
```python
import json

import signatures as sg


def _write_feelings(tmp_path, rows):
    p = tmp_path / "feeling.jsonl"
    with open(p, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    return str(p)


def test_escalation_slope_positive_when_rising():
    series = [(0, 2), (1, 3), (2, 4), (3, 6)]   # (step, score) rising
    assert sg.escalation_slope(series) > 0.9


def test_reciprocity_high_when_mirrored():
    ab = [(0, 2), (1, 3), (2, 5)]
    ba = [(0, 2), (1, 4), (2, 6)]   # tracks ab upward
    assert sg.reciprocity(ab, ba) > 0.9


def test_compute_signatures_from_feeling_log(tmp_path):
    rows = []
    for step, (s_ab, s_ba) in enumerate([(2, 2), (3, 4), (5, 5), (6, 6)]):
        rows.append({"step": step, "from": "Ada Rivera", "to": "Bea Rivera", "score": s_ab})
        rows.append({"step": step, "from": "Bea Rivera", "to": "Ada Rivera", "score": s_ba})
    path = _write_feelings(tmp_path, rows)
    out = sg.compute_signatures(path)
    assert out["escalation"]["Ada Rivera->Bea Rivera"] > 0     # rising
    assert out["reciprocity"] > 0.5                            # the two track each other
    assert "convergence" in out


def test_load_feelings_drops_unparsed_scores(tmp_path):
    rows = [{"step": 0, "from": "A", "to": "B", "score": None},
            {"step": 1, "from": "A", "to": "B", "score": 3}]
    path = _write_feelings(tmp_path, rows)
    series = sg.load_feelings(path)["A->B"]
    assert series == [(1, 3)]   # the None-score row is dropped
```

- [ ] **Step 2: Run to verify it fails** — `$PY -m pytest tests/test_signatures.py -q` → FAIL (`ModuleNotFoundError: No module named 'signatures'`).

- [ ] **Step 3: Implement** — create `signatures.py`:
```python
"""signatures.py — read the Girardian doubling signatures off the feeling-probe
trajectories. Plain trend math over the logged 1-7 scores; no LLM.
"""
import json

import numpy as np


def load_feelings(path):
    """Return {"<from>-><to>": [(step, score), ...]} for rows with a numeric score."""
    series = {}
    with open(path) as f:
        for line in f:
            r = json.loads(line)
            if r.get("score") is None:
                continue
            key = f'{r["from"]}->{r["to"]}'
            series.setdefault(key, []).append((int(r["step"]), float(r["score"])))
    for k in series:
        series[k].sort()
    return series


def escalation_slope(series):
    """Linear slope of score vs. step (>0 = hostility rising over time)."""
    if len(series) < 2:
        return 0.0
    steps = np.array([s for s, _ in series], dtype=float)
    scores = np.array([v for _, v in series], dtype=float)
    if np.ptp(steps) == 0:
        return 0.0
    return float(np.polyfit(steps, scores, 1)[0])


def _align(ab, ba):
    da, db = dict(ab), dict(ba)
    common = sorted(set(da) & set(db))
    return [da[s] for s in common], [db[s] for s in common]


def reciprocity(ab, ba):
    """Correlation of A->B and B->A score series aligned by step (mimesis of
    antagonism: each one's hostility tracks the other's). 0.0 if undefined."""
    xa, xb = _align(ab, ba)
    if len(xa) < 2 or np.std(xa) == 0 or np.std(xb) == 0:
        return 0.0
    return float(np.corrcoef(xa, xb)[0, 1])


def convergence(ab, ba):
    """Undifferentiation: how close the two directions' scores become by the end
    (1 / (1 + mean|A->B - B->A| over the last half)). Higher = more converged."""
    xa, xb = _align(ab, ba)
    if not xa:
        return 0.0
    half = xa[len(xa) // 2:], xb[len(xb) // 2:]
    diffs = [abs(a - b) for a, b in zip(*half)]
    return float(1.0 / (1.0 + (sum(diffs) / len(diffs)))) if diffs else 0.0


def compute_signatures(path):
    """Compute the signatures from a feeling.jsonl. Assumes a 2-agent pair."""
    series = load_feelings(path)
    keys = list(series.keys())
    escalation = {k: escalation_slope(series[k]) for k in keys}
    recip, conv = 0.0, 0.0
    if len(keys) == 2:
        recip = reciprocity(series[keys[0]], series[keys[1]])
        conv = convergence(series[keys[0]], series[keys[1]])
    return {"escalation": escalation, "reciprocity": recip, "convergence": conv}
```

- [ ] **Step 4: Run to verify it passes** — `$PY -m pytest tests/test_signatures.py -q` → PASS (4 passed). Then the full suite.

- [ ] **Step 5: Commit**
```bash
cd /Users/mkrolick/Documents/GitHub/SmallDesire
git add -f generative_agents/reverie/backend_server/signatures.py
git add generative_agents/reverie/backend_server/tests/test_signatures.py
git commit -m "feat: signatures.py — escalation/reciprocity/convergence over feeling trajectories"
```

---

### Task 4: Integration-gated live feeling-probe check

**Files:**
- Test: `tests/test_feelings_integration.py`

*(Real LLM via TokensPLS — gated on `RUN_INTEGRATION`. Generates a co-present pair, runs 1 instrumented step, asserts `feeling.jsonl` has parsed 1-7 scores.)*

- [ ] **Step 1: Write the test** — create `tests/test_feelings_integration.py`:
```python
import json
import os
import shutil

import pytest

import headless
import persona_factory as pf
from utils import fs_storage


@pytest.mark.skipif(not os.environ.get("RUN_INTEGRATION"),
                    reason="set RUN_INTEGRATION=1 with TokensPLS up + EMBED_API_KEY set")
def test_feeling_probe_writes_scores_live():
    sim = "smoke_feelings"
    folder = f"{fs_storage}/{sim}"
    run = f"{fs_storage}/{sim}_run"
    shutil.rmtree(folder, ignore_errors=True)
    shutil.rmtree(run, ignore_errors=True)
    try:
        pf.make_copresent_pair("house-rivera", 0.9, out_name=sim,
                               name_a="Ada Rivera", name_b="Bea Rivera")
        headless.run_headless_instrumented(sim, f"{sim}_run", 1, probe_every=1)
        feels = [json.loads(l) for l in open(f"{run}/measurements/feeling.jsonl")]
        assert len(feels) == 2
        for f in feels:
            assert f["score"] in range(1, 8)         # a real 1-7 score parsed from the live model
            assert isinstance(f["reason"], str) and f["reason"].strip()
        print("live feelings:", [(f["from"], f["to"], f["score"]) for f in feels])
    finally:
        shutil.rmtree(folder, ignore_errors=True)
        shutil.rmtree(run, ignore_errors=True)
```

- [ ] **Step 2: Confirm skip offline** — `$PY -m pytest tests/test_feelings_integration.py -v` → `1 skipped`.
- [ ] **Step 3: Full suite** — `$PY -m pytest tests/ -q` → all pass + (now 6) skipped.
- [ ] **Step 4: Commit**
```bash
cd /Users/mkrolick/Documents/GitHub/SmallDesire
git add generative_agents/reverie/backend_server/tests/test_feelings_integration.py
git commit -m "test: gated live feeling-probe score check"
```

---

## Self-Review

**Design coverage (the simplified measurement):**
- DV = "ask the agent how it feels, 1–7 + why" via LLM → Task 1 (`probe_feelings`), wired in Task 2. ✅
- The four signatures read off the score trajectories with simple math → Task 3 (escalation, reciprocity, convergence; objectlessness/"why goes circular" is left as a later text-analysis add-on, noted not built). ✅
- Runs on TokensPLS (via `provider_client`). ✅
- Sim-days / horizon: deliberately not fixed here — calibrated empirically during real runs.

**Placeholder scan:** none — complete code, commands, expected output.

**Type/name consistency:** `_parse_feeling`, `probe_feelings(personas, log, step, curr_time, n_retrieve=30)` defined in Task 1 and called in Task 2's wiring; `load_feelings`/`escalation_slope`/`reciprocity`/`convergence`/`compute_signatures` defined once in Task 3 and used consistently in its tests.

---

## Execution Handoff

(filled in after execution)
