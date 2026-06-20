# Shared-House Co-Presence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Place the two generated doubles in **one shared house** with separate bedrooms and shared common areas, so they naturally interact frequently — giving the doubling effect the co-presence it needs. **No conflict affordances** (per the spec revision): gossip/disparagement/exclusion emerge from natural talk, already captured by the Plan-2 instrumentation.

**Architecture:** The **Dorm for Oak Hill College** is already a shared house in the data — the upstream base houses two residents (Maria Lopez, Klaus Mueller) in separate rooms (`Maria Lopez's room`, `Klaus Mueller's room`) sharing a `common room`, `garden`, and two bathrooms. We make a 2-resident co-presence template from it (Maria + Klaus, Isabella removed), and parameterize `persona_factory.make_pair_base` to materialize generated pairs onto those two dorm slots. The result: both doubles live in the same building, pass through the same common areas, and meet — without any scripted togetherness.

**Tech Stack:** Python 3.13, stdlib, pytest. Builds on the merged Plan 3 `persona_factory.py`.

---

## Context (grounded facts — verified)

- 3-agent base `base_the_ville_isabella_maria_klaus` (vendored under `storage/`) has: Isabella → `the Ville:Isabella Rodriguez's apartment:main room`; **Maria → `the Ville:Dorm for Oak Hill College:Maria Lopez's room`; Klaus → `the Ville:Dorm for Oak Hill College:Klaus Mueller's room`.** The dorm sector's arenas (in a resident's spatial memory): `garden`, `<resident>'s room`, `woman's bathroom`, `common room`, `man's bathroom`.
- `persona_factory.make_pair_base(seed_id, delta, out_name, name_a, name_b, house=None, vocation="barista")` currently clones `_TEMPLATE_BASE = "base_the_ville_isabella_maria"` and maps onto `_TEMPLATE_PERSONAS = ["Isabella Rodriguez", "Maria Lopez"]` (who live in *different* homes — no co-presence). It already remaps name-embedded keys in `spatial_memory.json` + `living_area` + meta + env (Plan 3, hardened).
- Commands run from `generative_agents/reverie/backend_server/`; `PY=../../../.venv/bin/python`.

---

## File Structure

| Path | Responsibility |
|---|---|
| `generative_agents/environment/frontend_server/storage/base_the_ville_dorm_pair/` | **Create.** Co-presence template: Maria + Klaus, both in the dorm (Isabella removed). |
| `generative_agents/reverie/backend_server/persona_factory.py` | **Modify.** Parameterize `make_pair_base` with `template_base`/`template_personas`; add `CO_PRESENCE_TEMPLATE`/`CO_PRESENCE_PERSONAS`; add `make_copresent_pair` + `same_house`. |
| `generative_agents/reverie/backend_server/tests/test_copresence.py` | **Create.** Offline tests. |
| `generative_agents/reverie/backend_server/tests/test_copresence_integration.py` | **Create.** Integration-gated live co-presence check. |

---

### Task 1: Co-presence template base (Maria + Klaus, both dorm)

**Files:**
- Create: `generative_agents/environment/frontend_server/storage/base_the_ville_dorm_pair/` (from the 3-agent base)
- Test: `generative_agents/reverie/backend_server/tests/test_copresence.py`

- [ ] **Step 1: Write the failing test** — create `tests/test_copresence.py`:
```python
import json
import os

from utils import fs_storage

DORM = f"{fs_storage}/base_the_ville_dorm_pair"
RESIDENTS = {"Maria Lopez", "Klaus Mueller"}


def test_dorm_pair_base_is_consistent_and_copresent():
    meta = json.load(open(f"{DORM}/reverie/meta.json"))
    assert set(meta["persona_names"]) == RESIDENTS
    env = json.load(open(f"{DORM}/environment/0.json"))
    assert set(env.keys()) == RESIDENTS
    dirs = {d for d in os.listdir(f"{DORM}/personas") if not d.startswith(".")}
    assert dirs == RESIDENTS
    # both residents live in the SAME sector (the dorm) -> co-present
    sectors = set()
    for r in RESIDENTS:
        la = json.load(open(f"{DORM}/personas/{r}/bootstrap_memory/scratch.json"))["living_area"]
        sectors.add(la.split(":")[1])
    assert sectors == {"Dorm for Oak Hill College"}
```

- [ ] **Step 2: Run to verify it fails** — `$PY -m pytest tests/test_copresence.py -q` → FAIL (`FileNotFoundError` — the dorm-pair base doesn't exist).

- [ ] **Step 3: Create and trim the base** — from `base_the_ville_isabella_maria_klaus`, keep Maria + Klaus, drop Isabella:
```bash
cd /Users/mkrolick/Documents/GitHub/SmallDesire/generative_agents/environment/frontend_server/storage
cp -R base_the_ville_isabella_maria_klaus base_the_ville_dorm_pair
rm -rf "base_the_ville_dorm_pair/personas/Isabella Rodriguez"
```
Then edit `base_the_ville_dorm_pair/reverie/meta.json`: set `persona_names` to exactly `["Maria Lopez", "Klaus Mueller"]` (drop Isabella; keep all other fields).
Then edit `base_the_ville_dorm_pair/environment/0.json`: delete the `"Isabella Rodriguez"` entry (keep Maria + Klaus with their tile positions).
Verify both JSON files parse (`$PY -c "import json; json.load(open('reverie/meta.json'))"` etc. from the base dir).

- [ ] **Step 4: Run to verify it passes** — `$PY -m pytest tests/test_copresence.py -q` → PASS (1 passed). (Confirms both residents share the `Dorm for Oak Hill College` sector.)

- [ ] **Step 5: Commit**
```bash
cd /Users/mkrolick/Documents/GitHub/SmallDesire
git add -A
git commit -m "feat: shared-house co-presence template (dorm pair: Maria + Klaus)"
```
(The base is under `storage/base_*` so it's tracked per the `.gitignore` keep-rule.)

---

### Task 2: Parameterize `make_pair_base` with a template; add co-presence constants

**Files:**
- Modify: `persona_factory.py`
- Test: `tests/test_copresence.py`

- [ ] **Step 1: Write the failing test** — APPEND to `tests/test_copresence.py`:
```python
import shutil

import persona_factory as pf


def test_make_pair_base_with_dorm_template_is_copresent():
    out = "base_gen_copres_test"
    folder = f"{fs_storage}/{out}"
    shutil.rmtree(folder, ignore_errors=True)
    pf.make_pair_base("house-rivera", 0.4, out_name=out,
                      name_a="Ada Rivera", name_b="Bea Rivera",
                      template_base=pf.CO_PRESENCE_TEMPLATE,
                      template_personas=pf.CO_PRESENCE_PERSONAS)
    sectors = set()
    for nm in ("Ada Rivera", "Bea Rivera"):
        la = json.load(open(f"{folder}/personas/{nm}/bootstrap_memory/scratch.json"))["living_area"]
        sectors.add(la.split(":")[1])
    assert len(sectors) == 1   # both doubles in ONE sector -> co-present
    shutil.rmtree(folder, ignore_errors=True)
```

- [ ] **Step 2: Run to verify it fails** — `$PY -m pytest tests/test_copresence.py -k dorm_template -q` → FAIL (`AttributeError` on `pf.CO_PRESENCE_TEMPLATE` and/or unexpected `template_base` kwarg).

- [ ] **Step 3: Implement** — in `persona_factory.py`, add the constants next to `_TEMPLATE_BASE`:
```python
CO_PRESENCE_TEMPLATE = "base_the_ville_dorm_pair"
CO_PRESENCE_PERSONAS = ["Maria Lopez", "Klaus Mueller"]
```
and change the `make_pair_base` signature + the two internal references to use parameters (default to the existing single-home template for backward compatibility):
```python
def make_pair_base(seed_id, delta, out_name, name_a, name_b,
                   house=None, vocation="barista",
                   template_base=None, template_personas=None):
    """Clone a template base into storage/<out_name> and overwrite its two
    personas with a generated (seed, delta) pair. `template_base`/`template_personas`
    select which base to clone (default: the single-home Isabella/Maria template;
    pass CO_PRESENCE_TEMPLATE/CO_PRESENCE_PERSONAS for the shared dorm). Returns the names."""
    template_base = template_base or _TEMPLATE_BASE
    template_personas = template_personas or _TEMPLATE_PERSONAS
    house = house or f"the {name_a.split()[-1]} household"
    src = f"{fs_storage}/{template_base}"
    dst = f"{fs_storage}/{out_name}"
    shutil.rmtree(dst, ignore_errors=True)
    copyanything(src, dst)

    name_map = {template_personas[0]: name_a, template_personas[1]: name_b}

    tmp_names = {old: f"__tmp_{i}__" for i, old in enumerate(template_personas)}
    for old, tmp in tmp_names.items():
        os.rename(f"{dst}/personas/{old}", f"{dst}/personas/{tmp}")
    for old, new in name_map.items():
        os.rename(f"{dst}/personas/{tmp_names[old]}", f"{dst}/personas/{new}")

    a, b = perturb(seed_id, delta)
    traits_for = {name_a: a, name_b: b}

    for new_name, traits in traits_for.items():
        pdir = f"{dst}/personas/{new_name}"
        sm_path = f"{pdir}/bootstrap_memory/spatial_memory.json"
        with open(sm_path) as f:
            sm_text = f.read()
        for old, new in name_map.items():
            sm_text = sm_text.replace(old, new)
        with open(sm_path, "w") as f:
            f.write(sm_text)

        scratch_path = f"{pdir}/bootstrap_memory/scratch.json"
        scratch = _read_json(scratch_path)
        living_area = scratch.get("living_area") or ""
        for old, new in name_map.items():
            living_area = living_area.replace(old, new)
        if not living_area:
            living_area = f"the Ville:{name_a.split()[-1]} household:common room"
        iss = render_iss(traits, name=new_name, house=house,
                         living_area=living_area, vocation=vocation)
        scratch.update(iss)
        scratch["act_event"] = [new_name, None, None]
        _write_json(scratch_path, scratch)

    meta_path = f"{dst}/reverie/meta.json"
    meta = _read_json(meta_path)
    meta["persona_names"] = [name_a, name_b]
    meta["fork_sim_code"] = out_name
    _write_json(meta_path, meta)

    env_path = f"{dst}/environment/0.json"
    env = _read_json(env_path)
    env = {name_map.get(k, k): v for k, v in env.items()}
    _write_json(env_path, env)

    return [name_a, name_b]
```
(The only changes vs. the Plan-3 version: the two new params + defaulting them, and using `template_base`/`template_personas` in place of the hard-coded `_TEMPLATE_BASE`/`_TEMPLATE_PERSONAS`. Everything else is identical.)

- [ ] **Step 4: Run to verify it passes** — `$PY -m pytest tests/test_copresence.py -q` → PASS. Then the FULL suite `$PY -m pytest tests/ -q` → the Plan-3 `test_make_pair_base_writes_consistent_base` (default template) MUST still pass + all others. Expect all pass + (now 4) skipped.

- [ ] **Step 5: Commit**
```bash
cd /Users/mkrolick/Documents/GitHub/SmallDesire
git add -f generative_agents/reverie/backend_server/persona_factory.py
git add generative_agents/reverie/backend_server/tests/test_copresence.py
git commit -m "feat: parameterize make_pair_base with a co-presence template"
```

---

### Task 3: `make_copresent_pair` convenience + `same_house` check

**Files:**
- Modify: `persona_factory.py`
- Test: `tests/test_copresence.py`

- [ ] **Step 1: Write the failing test** — APPEND:
```python
def test_make_copresent_pair_and_same_house():
    out = "base_gen_copres_helper"
    folder = f"{fs_storage}/{out}"
    shutil.rmtree(folder, ignore_errors=True)
    pf.make_copresent_pair("house-okafor", 0.6, out_name=out,
                           name_a="Cy Okafor", name_b="Dee Okafor")
    assert pf.same_house(folder) is True
    shutil.rmtree(folder, ignore_errors=True)


def test_same_house_false_for_single_home_template():
    out = "base_gen_singlehome"
    folder = f"{fs_storage}/{out}"
    shutil.rmtree(folder, ignore_errors=True)
    pf.make_pair_base("house-rivera", 0.4, out_name=out,
                      name_a="Ada Rivera", name_b="Bea Rivera")   # default single-home template
    assert pf.same_house(folder) is False     # apartment vs dorm -> different sectors
    shutil.rmtree(folder, ignore_errors=True)
```

- [ ] **Step 2: Run to verify it fails** — `$PY -m pytest tests/test_copresence.py -k "copresent_pair or same_house" -q` → FAIL (no `make_copresent_pair`/`same_house`).

- [ ] **Step 3: Implement** — add to `persona_factory.py`:
```python
def same_house(base_path):
    """True iff every persona in the materialized base lives in the same sector."""
    sectors = set()
    personas_dir = f"{base_path}/personas"
    for name in os.listdir(personas_dir):
        if name.startswith("."):
            continue
        la = _read_json(f"{personas_dir}/{name}/bootstrap_memory/scratch.json").get("living_area", "")
        parts = la.split(":")
        sectors.add(parts[1] if len(parts) > 1 else la)
    return len(sectors) == 1


def make_copresent_pair(seed_id, delta, out_name, name_a, name_b, vocation="barista"):
    """Materialize a (seed, delta) pair sharing the dorm (co-present)."""
    return make_pair_base(seed_id, delta, out_name, name_a, name_b,
                          house="the dorm", vocation=vocation,
                          template_base=CO_PRESENCE_TEMPLATE,
                          template_personas=CO_PRESENCE_PERSONAS)
```

- [ ] **Step 4: Run to verify it passes** — `$PY -m pytest tests/test_copresence.py -q` → PASS. Then the full suite `$PY -m pytest tests/ -q`.

- [ ] **Step 5: Commit**
```bash
cd /Users/mkrolick/Documents/GitHub/SmallDesire
git add -f generative_agents/reverie/backend_server/persona_factory.py
git add generative_agents/reverie/backend_server/tests/test_copresence.py
git commit -m "feat: make_copresent_pair + same_house check"
```

---

### Task 4: Integration-gated live co-presence check

**Files:**
- Test: `generative_agents/reverie/backend_server/tests/test_copresence_integration.py`

*(Real LLM — gated on `RUN_INTEGRATION`. Generates a co-present dorm pair and runs a few instrumented steps; confirms the run produces measurements and the two share a sector. NOTE: a *conversation actually occurring* depends on the agents' schedules aligning in a common area, which can take many sim-steps — so this test asserts the run completes + the pair is co-present + measurement logs are written, and merely REPORTS whether a conversation was captured, rather than asserting one in a short run.)*

- [ ] **Step 1: Write the test** — create `tests/test_copresence_integration.py`:
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
def test_copresent_pair_runs_and_logs():
    sim = "smoke_copresence"
    folder = f"{fs_storage}/{sim}"
    shutil.rmtree(folder, ignore_errors=True)
    pf.make_copresent_pair("house-rivera", 0.0, out_name=sim,
                           name_a="Ada Rivera", name_b="Bea Rivera")
    assert pf.same_house(folder) is True
    # fork the generated base into a run and step it instrumented
    headless.run_headless_instrumented(sim, f"{sim}_run", 2, probe_every=1)
    rel = f"{fs_storage}/{sim}_run/measurements/relationship_summary.jsonl"
    assert os.path.exists(rel)
    lines = [json.loads(l) for l in open(rel)]
    assert len(lines) >= 2     # both ordered-pair probes, at least one step
    convo_path = f"{fs_storage}/{sim}_run/measurements/conversation.jsonl"
    n_convos = len(open(convo_path).read().splitlines()) if os.path.exists(convo_path) else 0
    print(f"co-presence run: {len(lines)} relationship probes, {n_convos} conversations captured")
    shutil.rmtree(folder, ignore_errors=True)
    shutil.rmtree(f"{fs_storage}/{sim}_run", ignore_errors=True)
```

- [ ] **Step 2: Confirm it collects + skips offline** — `$PY -m pytest tests/test_copresence_integration.py -v` → `1 skipped`.

- [ ] **Step 3: Full suite** — `$PY -m pytest tests/ -q` → all pass + (now 5) skipped.

- [ ] **Step 4: Commit**
```bash
cd /Users/mkrolick/Documents/GitHub/SmallDesire
git add generative_agents/reverie/backend_server/tests/test_copresence_integration.py
git commit -m "test: integration-gated live co-presence run check"
```

---

## Self-Review

**Spec coverage (spec §3.3, revised):**
- Co-presence so natural talk happens → the dorm template + `make_copresent_pair` (Tasks 1–3). ✅
- No conflict affordances → nothing of the sort is added; conflict is left to emerge and is captured by Plan-2 instrumentation. ✅
- Shared-house realized (the deferred Plan-3 item) → both doubles in one sector with shared common areas. ✅

**Placeholder scan:** none — complete code + commands + expected output.

**Type/name consistency:** `make_pair_base(..., template_base=None, template_personas=None)` defaults preserve Plan-3 behavior; `CO_PRESENCE_TEMPLATE`/`CO_PRESENCE_PERSONAS`, `make_copresent_pair(...)`, and `same_house(base_path)` are defined once and used consistently across Tasks 2–4.

---

## Execution Handoff

(filled in after execution)
