# Instrumentation & Logging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Capture the experiment's measurement signals — per-pair relationship summaries (the primary attitude probe), reflection thoughts about the other agent, and conversation transcripts — to structured per-run JSONL logs, without modifying the validated cognition.

**Architecture:** A self-contained `instrumentation.py` module: a `MeasurementLog` (writes `storage/<sim>/measurements/<kind>.jsonl`), three pure-ish capture helpers, and an on-demand relationship *probe* (computes A→B and B→A attitude summaries at a configurable cadence — a dense longitudinal DV even when the agents don't converse). An instrumented runner in `headless.py` wires them around `process_step`. We do **not** monkeypatch the cognition: reflections and conversations are read from the agents' own memory/output after each step, and the relationship probe calls the existing `generate_summarize_agent_relationship` on demand.

**Tech Stack:** Python 3.13, stdlib `json`/`os`, pytest. All unit tests are offline (the probe's LLM call is stubbed; the live path is an integration-gated test).

---

## Context (grounded facts — do not re-derive)

This plan builds on Plan 1 (merged to `main`). The backend imports cleanly; CWD for the backend = `generative_agents/reverie/backend_server/`; tests run there with `../../../.venv/bin/python -m pytest ...`.

Verified hook points (from the generative_agents code, on `main`):
- **Relationship summary (primary attitude probe):** `generate_summarize_agent_relationship(init_persona, target_persona, retrieved)` in `persona/cognitive_modules/converse.py` returns a single free-text string = init_persona's attitude/knowledge about target_persona. Retrieval is `new_retrieve(persona, [target_name], n)` from `persona/cognitive_modules/retrieve.py`.
- **Reflections:** reflection thoughts are `ConceptNode`s stored in `persona.a_mem.seq_thought` (a list; **newest is prepended at index 0**). `ConceptNode` fields used here: `.type` (`'thought'`/`'event'`/`'chat'`), `.created` (datetime), `.description` (str), `.poignancy` (int), `.keywords` (set), `.filling` (list of evidence node-ids), `.subject`/`.object` (str).
- **Conversations:** after `process_step`, a conversation (if any) is in `movements["persona"][name]["chat"]` — a list of `[speaker, utterance]` pairs, or `None`. Both participants carry the same transcript.
- **Time formatting:** the sim formats time as `curr_time.strftime("%B %d, %Y, %H:%M:%S")`.

---

## File Structure

| Path | Responsibility |
|---|---|
| `generative_agents/reverie/backend_server/instrumentation.py` | **Create.** `MeasurementLog`, `capture_new_reflections`, `capture_conversations`, `probe_relationships`, `_fmt_time`. |
| `generative_agents/reverie/backend_server/headless.py` | **Modify.** Add `run_headless_instrumented(...)` that wires the captures + probe around `process_step`. |
| `generative_agents/reverie/backend_server/tests/test_instrumentation.py` | **Create.** Unit tests (offline, fakes/stubs). |
| `generative_agents/reverie/backend_server/tests/test_instrumented_run_integration.py` | **Create.** Integration-gated end-to-end (real LLM). |

All commands below run from `generative_agents/reverie/backend_server/` unless noted. `PY=../../../.venv/bin/python`.

---

### Task 1: `MeasurementLog` — structured JSONL writer

**Files:**
- Create: `instrumentation.py`
- Test: `tests/test_instrumentation.py`

- [ ] **Step 1: Write the failing test** — create `tests/test_instrumentation.py`:
```python
import datetime
import json

import instrumentation
from utils import fs_storage


def test_measurement_log_writes_jsonl(tmp_path, monkeypatch):
    # Point fs_storage-derived dir at a temp sim folder via a fake sim_code under storage.
    sim = "test_measlog_unit"
    log = instrumentation.MeasurementLog(sim)
    t = datetime.datetime(2023, 2, 13, 0, 0, 10)
    rec = log.record("relationship_summary", 3, t, {"from": "A", "to": "B", "summary": "wary"})
    path = f"{fs_storage}/{sim}/measurements/relationship_summary.jsonl"
    line = open(path).read().strip()
    parsed = json.loads(line)
    assert parsed["step"] == 3
    assert parsed["kind"] == "relationship_summary"
    assert parsed["curr_time"] == "February 13, 2023, 00:00:10"
    assert parsed["from"] == "A" and parsed["to"] == "B" and parsed["summary"] == "wary"
    assert rec == parsed
    import shutil
    shutil.rmtree(f"{fs_storage}/{sim}", ignore_errors=True)
```

- [ ] **Step 2: Run test to verify it fails** — `$PY -m pytest tests/test_instrumentation.py::test_measurement_log_writes_jsonl -q` → FAIL (`ModuleNotFoundError: No module named 'instrumentation'`).

- [ ] **Step 3: Implement** — create `instrumentation.py`:
```python
"""instrumentation.py — measurement logging for the SmallDesire experiment.

Captures the attitude/affect signals (relationship summaries, reflections about
the other agent, conversation transcripts) to per-run JSONL logs under
storage/<sim>/measurements/. Reads the agents' own memory/output; does NOT
modify the validated cognition.
"""
import json
import os

from utils import fs_storage


def _fmt_time(t):
    return t.strftime("%B %d, %Y, %H:%M:%S") if hasattr(t, "strftime") else str(t)


class MeasurementLog:
    """Appends newline-delimited JSON records to storage/<sim>/measurements/<kind>.jsonl."""

    def __init__(self, sim_code):
        self.dir = f"{fs_storage}/{sim_code}/measurements"
        os.makedirs(self.dir, exist_ok=True)

    def record(self, kind, step, curr_time, payload):
        rec = {"step": step, "curr_time": _fmt_time(curr_time), "kind": kind}
        rec.update(payload)
        with open(f"{self.dir}/{kind}.jsonl", "a") as f:
            f.write(json.dumps(rec) + "\n")
        return rec
```

- [ ] **Step 4: Run test to verify it passes** — `$PY -m pytest tests/test_instrumentation.py -q` → PASS (1 passed).

- [ ] **Step 5: Commit**
```bash
cd /Users/mkrolick/Documents/GitHub/SmallDesire
git add -f generative_agents/reverie/backend_server/instrumentation.py
git add generative_agents/reverie/backend_server/tests/test_instrumentation.py
git commit -m "feat: MeasurementLog (structured JSONL measurement writer)"
```

---

### Task 2: `capture_new_reflections` — log new thoughts about the other agent

**Files:**
- Modify: `instrumentation.py`
- Test: `tests/test_instrumentation.py`

- [ ] **Step 1: Write the failing test** — append to `tests/test_instrumentation.py`:
```python
import types

import datetime as _dt


def _fake_node(description, keywords, subject="", obj="", poignancy=5, filling=None):
    return types.SimpleNamespace(
        description=description, keywords=set(keywords), subject=subject, object=obj,
        poignancy=poignancy, filling=filling or [], created=_dt.datetime(2023, 2, 13, 0, 1, 0),
    )


def _fake_persona(name, first_name, seq_thought):
    scratch = types.SimpleNamespace(name=name, first_name=first_name)
    a_mem = types.SimpleNamespace(seq_thought=list(seq_thought))
    return types.SimpleNamespace(scratch=scratch, a_mem=a_mem)


def test_capture_new_reflections_logs_only_partner_refs(monkeypatch):
    sim = "test_capture_refl_unit"
    log = instrumentation.MeasurementLog(sim)
    maria = _fake_persona("Maria Lopez", "Maria", [])
    isabella = _fake_persona("Isabella Rodriguez", "Isabella", [])
    # newest prepended at index 0: a thought about Maria, then an unrelated thought
    isabella.a_mem.seq_thought = [
        _fake_node("Isabella finds Maria competitive", ["Maria", "competitive"], "Isabella", "Maria", 8),
        _fake_node("Isabella likes coffee", ["coffee"], "Isabella", "coffee", 2),
    ]
    cursor = instrumentation.capture_new_reflections(
        isabella, [maria], log, step=2, curr_time=_dt.datetime(2023, 2, 13, 0, 1, 0), cursor=0)
    assert cursor == 2  # cursor advances to len(seq_thought)
    path = f"{instrumentation.fs_storage}/{sim}/measurements/reflection.jsonl"
    lines = [__import__("json").loads(l) for l in open(path)]
    assert len(lines) == 1  # only the Maria-referencing thought logged
    r = lines[0]
    assert r["persona"] == "Isabella Rodriguez" and r["about"] == "Maria Lopez"
    assert r["poignancy"] == 8 and "Maria" in r["description"]
    import shutil
    shutil.rmtree(f"{instrumentation.fs_storage}/{sim}", ignore_errors=True)


def test_capture_new_reflections_respects_cursor(monkeypatch):
    sim = "test_capture_refl_cursor"
    log = instrumentation.MeasurementLog(sim)
    maria = _fake_persona("Maria Lopez", "Maria", [])
    isabella = _fake_persona("Isabella Rodriguez", "Isabella", [
        _fake_node("old thought about Maria", ["Maria"], "Isabella", "Maria", 5),
    ])
    # cursor already at 1 -> the existing node is NOT re-logged
    cursor = instrumentation.capture_new_reflections(
        isabella, [maria], log, step=5, curr_time=_dt.datetime(2023, 2, 13, 0, 5, 0), cursor=1)
    assert cursor == 1
    path = f"{instrumentation.fs_storage}/{sim}/measurements/reflection.jsonl"
    import os
    assert not os.path.exists(path)  # nothing new -> no file written
    import shutil
    shutil.rmtree(f"{instrumentation.fs_storage}/{sim}", ignore_errors=True)
```

- [ ] **Step 2: Run to verify it fails** — `$PY -m pytest tests/test_instrumentation.py -k capture_new_reflections -q` → FAIL (`AttributeError: module 'instrumentation' has no attribute 'capture_new_reflections'`).

- [ ] **Step 3: Implement** — add to `instrumentation.py`:
```python
def capture_new_reflections(persona, other_personas, log, step, curr_time, cursor):
    """Log NEW thought nodes (those added since `cursor`) that reference another
    persona. seq_thought prepends newest at index 0, so the newest
    (len - cursor) entries are the new ones. Returns the updated cursor."""
    seq = persona.a_mem.seq_thought
    n_new = len(seq) - cursor
    if n_new <= 0:
        return len(seq)
    new_nodes = seq[:n_new]
    for node in new_nodes:
        text = " ".join([
            str(node.description), " ".join(node.keywords),
            str(node.subject), str(node.object),
        ]).lower()
        for other in other_personas:
            if other.scratch.first_name.lower() in text or other.scratch.name.lower() in text:
                log.record("reflection", step, curr_time, {
                    "persona": persona.scratch.name,
                    "about": other.scratch.name,
                    "description": node.description,
                    "poignancy": node.poignancy,
                    "keywords": list(node.keywords),
                    "evidence": list(node.filling),
                    "created": _fmt_time(node.created),
                })
                break
    return len(seq)
```

- [ ] **Step 4: Run to verify it passes** — `$PY -m pytest tests/test_instrumentation.py -k capture_new_reflections -q` → PASS (2 passed).

- [ ] **Step 5: Commit**
```bash
cd /Users/mkrolick/Documents/GitHub/SmallDesire
git add -f generative_agents/reverie/backend_server/instrumentation.py
git add generative_agents/reverie/backend_server/tests/test_instrumentation.py
git commit -m "feat: capture reflection thoughts about the other agent"
```

---

### Task 3: `capture_conversations` — log conversation transcripts (deduped)

**Files:**
- Modify: `instrumentation.py`
- Test: `tests/test_instrumentation.py`

- [ ] **Step 1: Write the failing test** — append:
```python
def test_capture_conversations_logs_unique_transcripts():
    sim = "test_capture_convo_unit"
    log = instrumentation.MeasurementLog(sim)
    convo = [["Isabella", "Hi Maria"], ["Maria", "Hi Isabella"]]
    movements = {"persona": {
        "Isabella Rodriguez": {"movement": [1, 2], "chat": convo},
        "Maria Lopez": {"movement": [3, 4], "chat": convo},   # same transcript (shared)
    }, "meta": {}}
    instrumentation.capture_conversations(
        movements, log, step=4, curr_time=__import__("datetime").datetime(2023, 2, 13, 0, 0, 40))
    path = f"{instrumentation.fs_storage}/{sim}/measurements/conversation.jsonl"
    lines = [__import__("json").loads(l) for l in open(path)]
    assert len(lines) == 1  # deduped: the shared transcript logged once
    assert lines[0]["transcript"] == convo
    assert sorted(lines[0]["participants"]) == ["Isabella Rodriguez", "Maria Lopez"]
    import shutil
    shutil.rmtree(f"{instrumentation.fs_storage}/{sim}", ignore_errors=True)


def test_capture_conversations_ignores_none_chat():
    sim = "test_capture_convo_none"
    log = instrumentation.MeasurementLog(sim)
    movements = {"persona": {
        "Isabella Rodriguez": {"movement": [1, 2], "chat": None},
        "Maria Lopez": {"movement": [3, 4], "chat": None},
    }, "meta": {}}
    instrumentation.capture_conversations(
        movements, log, step=1, curr_time=__import__("datetime").datetime(2023, 2, 13, 0, 0, 10))
    import os
    assert not os.path.exists(f"{instrumentation.fs_storage}/{sim}/measurements/conversation.jsonl")
    import shutil
    shutil.rmtree(f"{instrumentation.fs_storage}/{sim}", ignore_errors=True)
```

- [ ] **Step 2: Run to verify it fails** — `$PY -m pytest tests/test_instrumentation.py -k capture_conversations -q` → FAIL (no attribute `capture_conversations`).

- [ ] **Step 3: Implement** — add to `instrumentation.py`:
```python
def capture_conversations(movements, log, step, curr_time):
    """Log each non-empty conversation transcript once (both participants share
    the same transcript object, so dedup by transcript content within the step)."""
    seen = set()
    persona_block = movements.get("persona", {})
    for name, m in persona_block.items():
        chat = m.get("chat")
        if not chat:
            continue
        key = json.dumps(chat, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        participants = [n for n, mm in persona_block.items()
                        if json.dumps(mm.get("chat"), sort_keys=True) == key]
        log.record("conversation", step, curr_time, {
            "participants": participants,
            "transcript": chat,
        })
```

- [ ] **Step 4: Run to verify it passes** — `$PY -m pytest tests/test_instrumentation.py -k capture_conversations -q` → PASS (2 passed).

- [ ] **Step 5: Commit**
```bash
cd /Users/mkrolick/Documents/GitHub/SmallDesire
git add -f generative_agents/reverie/backend_server/instrumentation.py
git add generative_agents/reverie/backend_server/tests/test_instrumentation.py
git commit -m "feat: capture deduped conversation transcripts"
```

---

### Task 4: `probe_relationships` — on-demand A→B / B→A attitude DV

**Files:**
- Modify: `instrumentation.py`
- Test: `tests/test_instrumentation.py`

- [ ] **Step 1: Write the failing test** — append:
```python
def test_probe_relationships_logs_each_ordered_pair(monkeypatch):
    sim = "test_probe_unit"
    log = instrumentation.MeasurementLog(sim)

    def fake_new_retrieve(persona, focal_points, n_count=30):
        return {focal_points[0]: []}

    calls = []
    def fake_summarize(a, b, retrieved):
        calls.append((a.scratch.name, b.scratch.name))
        return f"{a.scratch.name} thinks {b.scratch.name} is a rival"

    monkeypatch.setattr(instrumentation, "new_retrieve", fake_new_retrieve)
    monkeypatch.setattr(instrumentation.converse, "generate_summarize_agent_relationship", fake_summarize)

    isabella = _fake_persona("Isabella Rodriguez", "Isabella", [])
    maria = _fake_persona("Maria Lopez", "Maria", [])
    personas = {"Isabella Rodriguez": isabella, "Maria Lopez": maria}
    instrumentation.probe_relationships(
        personas, log, step=6, curr_time=__import__("datetime").datetime(2023, 2, 13, 0, 1, 0))

    # both ordered pairs probed
    assert set(calls) == {("Isabella Rodriguez", "Maria Lopez"), ("Maria Lopez", "Isabella Rodriguez")}
    path = f"{instrumentation.fs_storage}/{sim}/measurements/relationship_summary.jsonl"
    lines = [__import__("json").loads(l) for l in open(path)]
    assert len(lines) == 2
    assert all(l["source"] == "probe" for l in lines)
    assert {(l["from"], l["to"]) for l in lines} == set(calls)
    import shutil
    shutil.rmtree(f"{instrumentation.fs_storage}/{sim}", ignore_errors=True)
```

- [ ] **Step 2: Run to verify it fails** — `$PY -m pytest tests/test_instrumentation.py -k probe_relationships -q` → FAIL (no attribute `probe_relationships`, and/or no `new_retrieve`/`converse` on the module).

- [ ] **Step 3: Implement** — add the imports at the TOP of `instrumentation.py` (below the existing `from utils import fs_storage`):
```python
from persona.cognitive_modules import converse
from persona.cognitive_modules.retrieve import new_retrieve
```
and add the function:
```python
def probe_relationships(personas, log, step, curr_time, n_retrieve=50):
    """On-demand attitude DV: for each ordered pair (A,B), retrieve A's memories
    about B and compute A's relationship summary, logging it with source='probe'.
    This is the dense longitudinal signal (independent of whether they conversed)."""
    names = list(personas.keys())
    for a_name in names:
        for b_name in names:
            if a_name == b_name:
                continue
            a, b = personas[a_name], personas[b_name]
            retrieved = new_retrieve(a, [b.scratch.name], n_retrieve)
            summary = converse.generate_summarize_agent_relationship(a, b, retrieved)
            log.record("relationship_summary", step, curr_time, {
                "from": a_name, "to": b_name, "summary": summary, "source": "probe",
            })
```

- [ ] **Step 4: Run to verify it passes** — `$PY -m pytest tests/test_instrumentation.py -k probe_relationships -q` → PASS (1 passed). Also run the whole instrumentation test file: `$PY -m pytest tests/test_instrumentation.py -q` → all pass.

- [ ] **Step 5: Commit**
```bash
cd /Users/mkrolick/Documents/GitHub/SmallDesire
git add -f generative_agents/reverie/backend_server/instrumentation.py
git add generative_agents/reverie/backend_server/tests/test_instrumentation.py
git commit -m "feat: on-demand relationship probe (per-ordered-pair attitude DV)"
```

---

### Task 5: `run_headless_instrumented` — wire captures + probe around the loop

**Files:**
- Modify: `headless.py`
- Test: `tests/test_instrumentation.py`

- [ ] **Step 1: Write the failing test** — append (drives a real ReverieServer with stubbed `move`, and stubs the probe's LLM via the cognition seam, so it stays offline):
```python
def test_run_headless_instrumented_writes_measurements(monkeypatch):
    import shutil
    import reverie
    import headless
    import instrumentation as instr

    sim = "test_instrumented_run"
    folder = f"{instr.fs_storage}/{sim}"
    shutil.rmtree(folder, ignore_errors=True)

    # Stub the probe's LLM seam so no network is hit.
    monkeypatch.setattr(instr, "new_retrieve", lambda persona, fp, n_count=30: {fp[0]: []})
    monkeypatch.setattr(instr.converse, "generate_summarize_agent_relationship",
                        lambda a, b, retrieved: f"{a.scratch.name}->{b.scratch.name}")

    # Stub persona cognition (no LLM in move).
    orig_init = reverie.ReverieServer.__init__
    def patched_init(self, fork, sim_code):
        orig_init(self, fork, sim_code)
        for p in self.personas.values():
            monkeypatch.setattr(p, "move", lambda maze, personas, tile, t: ((1, 2), "S", "idle @ home"))
    monkeypatch.setattr(reverie.ReverieServer, "__init__", patched_init)

    headless.run_headless_instrumented("base_the_ville_isabella_maria", sim, 2, probe_every=1)

    import json as _json
    rel = [_json.loads(l) for l in open(f"{folder}/measurements/relationship_summary.jsonl")]
    # 2 ordered pairs x 2 steps = 4 probe records
    assert len(rel) == 4
    assert all(r["source"] == "probe" for r in rel)
    assert {(r["from"], r["to"]) for r in rel} == {
        ("Isabella Rodriguez", "Maria Lopez"), ("Maria Lopez", "Isabella Rodriguez")}
    shutil.rmtree(folder, ignore_errors=True)
```

- [ ] **Step 2: Run to verify it fails** — `$PY -m pytest tests/test_instrumentation.py -k run_headless_instrumented -q` → FAIL (`AttributeError: module 'headless' has no attribute 'run_headless_instrumented'`).

- [ ] **Step 3: Implement** — in `headless.py`, add `import instrumentation` near the top imports, and add this function (after `run_headless`):
```python
def run_headless_instrumented(fork_sim_code, sim_code, n_steps, probe_every=1):
    """Like run_headless, but captures measurements each step:
      - new reflection thoughts about the other agent,
      - conversation transcripts,
      - (every `probe_every` steps) an on-demand relationship summary per ordered pair.
    Set probe_every=0 to disable the on-demand probe. Returns the server."""
    rs = ReverieServer(fork_sim_code, sim_code)
    log = instrumentation.MeasurementLog(sim_code)
    cursors = {name: 0 for name in rs.personas}
    sim_folder = f"{fs_storage}/{sim_code}"
    # ReverieServer.__init__ already read environment/<step>.json to place personas;
    # process_step needs that same full env dict, so we re-read it for the first step.
    with open(f"{sim_folder}/environment/{rs.step}.json") as f:
        env = json.load(f)
    for i in range(n_steps):
        step = rs.step  # label measurements with the step being processed (pre-increment)
        movements = rs.process_step(env)
        for name, persona in rs.personas.items():
            others = [p for n, p in rs.personas.items() if n != name]
            cursors[name] = instrumentation.capture_new_reflections(
                persona, others, log, step, rs.curr_time, cursors[name])
        instrumentation.capture_conversations(movements, log, step, rs.curr_time)
        if probe_every and (i % probe_every == 0):
            instrumentation.probe_relationships(rs.personas, log, step, rs.curr_time)
        env = next_env_from_movements(movements)
    rs.save()
    return rs
```

- [ ] **Step 4: Run to verify it passes** — `$PY -m pytest tests/test_instrumentation.py -k run_headless_instrumented -q` → PASS (1 passed).

- [ ] **Step 5: Run the full offline suite** — `$PY -m pytest tests/ -q` → all pass + 1 skipped (the prior Task-12 smoke). No regressions.

- [ ] **Step 6: Commit**
```bash
cd /Users/mkrolick/Documents/GitHub/SmallDesire
git add -f generative_agents/reverie/backend_server/headless.py
git add generative_agents/reverie/backend_server/tests/test_instrumentation.py
git commit -m "feat: run_headless_instrumented (capture reflections, conversations, probe)"
```

---

### Task 6: Integration-gated instrumented smoke

**Files:**
- Test: `tests/test_instrumented_run_integration.py`

*(Real LLM/embeddings; skipped unless `RUN_INTEGRATION=1` with TokensPLS up + `EMBED_API_KEY`. Proves the measurement logs actually get written from a live 1-step run.)*

- [ ] **Step 1: Write the test** — create `tests/test_instrumented_run_integration.py`:
```python
import json
import os
import shutil

import pytest

import headless
from utils import fs_storage


@pytest.mark.skipif(not os.environ.get("RUN_INTEGRATION"),
                    reason="set RUN_INTEGRATION=1 with TokensPLS up + EMBED_API_KEY set")
def test_instrumented_run_writes_relationship_log():
    sim = "smoke_instrumented"
    folder = f"{fs_storage}/{sim}"
    shutil.rmtree(folder, ignore_errors=True)
    headless.run_headless_instrumented("base_the_ville_isabella_maria", sim, 1, probe_every=1)
    rel_path = f"{folder}/measurements/relationship_summary.jsonl"
    assert os.path.exists(rel_path)
    lines = [json.loads(l) for l in open(rel_path)]
    # one real step, probe_every=1 -> 2 ordered-pair probe records, each a non-empty string
    assert len(lines) == 2
    for r in lines:
        assert r["source"] == "probe"
        assert isinstance(r["summary"], str) and r["summary"].strip()
        assert (r["from"], r["to"]) in {
            ("Isabella Rodriguez", "Maria Lopez"), ("Maria Lopez", "Isabella Rodriguez")}
    shutil.rmtree(folder, ignore_errors=True)
```

- [ ] **Step 2: Confirm it collects + skips cleanly offline** — `$PY -m pytest tests/test_instrumented_run_integration.py -v` → `1 skipped` (collected, not errored).

- [ ] **Step 3: Full suite** — `$PY -m pytest tests/ -q` → all pass + 2 skipped (the two integration smokes).

- [ ] **Step 4: Commit**
```bash
cd /Users/mkrolick/Documents/GitHub/SmallDesire
git add generative_agents/reverie/backend_server/tests/test_instrumented_run_integration.py
git commit -m "test: integration-gated instrumented run smoke"
```

---

## Self-Review

**Spec coverage (spec §5 measurement battery):**
- Relationship-summary trajectory (primary attitude probe) → Task 4 (`probe_relationships`) + Task 5 cadence. ✅
- Reflection-memory sentiment (the "latent" private channel) → Task 2 (`capture_new_reflections`). ✅
- Conversation transcripts (for the blind judge later) → Task 3 (`capture_conversations`). ✅
- Per-agent isolation: each capture reads a single persona's own memory; the probe computes A→B from A's own retrieval — naturally private. ✅
- Behavioral proxies, the blind judge panel, the four signature computations, and the sycophancy baseline are **deferred to Plan 5** (this plan provides the raw logs they consume).

**Placeholder scan:** none — every step has complete code, commands, and expected output.

**Type/name consistency:** `MeasurementLog.record(kind, step, curr_time, payload)` is defined in Task 1 and called identically in Tasks 2–5; `capture_new_reflections(persona, other_personas, log, step, curr_time, cursor) -> cursor`, `capture_conversations(movements, log, step, curr_time)`, and `probe_relationships(personas, log, step, curr_time, n_retrieve=50)` are defined once and called with matching signatures in `run_headless_instrumented`. The module-level `converse` / `new_retrieve` names referenced by the probe test's monkeypatch are exactly the names imported in Task 4.

---

## Execution Handoff

(filled in by the assistant after the plan is approved/executed)
