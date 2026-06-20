# Persona Generation & δ-Perturbation Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate pairs of "same-house" Smallville personas whose identities differ by a controlled distance δ — the experiment's independent variable — and materialize a runnable 2-agent base sim for each (seed, δ), with manipulation-check metrics.

**Architecture:** A self-contained `persona_factory.py`. Identity is a vector of continuous personality/value traits in [0,1] over a **shared house context** (same surname/house, origin story, living area, vocation domain — held constant so the manipulation is identity-*similarity*, not proximity). A deterministic symmetric perturbation places two personas δ apart around a per-seed midpoint (neither is "the deviant"). A **length-matched** renderer turns each trait vector into the scratch ISS fields (only trait-derived single words vary, so verbosity can't confound similarity). A materializer writes a runnable 2-agent base by cloning `base_the_ville_isabella_maria` and overwriting the two personas' identity fields. Manipulation check = designed δ vs. realized trait distance vs. embedding distance of the rendered personas.

**Tech Stack:** Python 3.13, stdlib (`hashlib`, `json`, `shutil`), `provider_client.get_embedding` (live OpenAI embeddings) for the manipulation check, pytest.

---

## Design decisions (sensible defaults — documented because they shape the IV)

- **8 trait dimensions** in [0,1]: `warmth, ambition, dominance, agreeableness, conscientiousness, openness, sociability, volatility`. (Big-Five-adjacent + dominance/warmth/volatility, which are the traits most relevant to rivalry.)
- **Shared house context** (constant across a pair): a house/surname, a one-line shared `origin_story` template, a shared `living_area` path (reused from the template base), and a shared vocation domain. Only the 8 traits vary between the pair.
- **Determinism:** all randomness derives from `hashlib` of the `seed_id` string — same seed ⇒ same midpoint + same perturbation direction ⇒ fully reproducible (no `random`/time).
- **Distance:** trait distance = Euclidean over the 8-D vector, normalized by √8 so it lands in ~[0,1]. δ is the *designed* pair distance; the realized distance is measured (clamping to [0,1] can shrink it) and reported.
- **Word banks:** each trait has a 5-bucket adjective bank (value → one adjective). Rendering always emits exactly one adjective per slot ⇒ constant token counts (length-matched).
- **v1 scoping:** vary temperament/values only; vocation + spatial layout are inherited from the template base (true shared-bedroom co-location is a later refinement). Stated so it's explicit.

---

## File Structure

| Path | Responsibility |
|---|---|
| `generative_agents/reverie/backend_server/persona_factory.py` | **Create.** Trait schema, word banks, `seed_midpoint`, `perturb`, `trait_distance`, `render_iss`, `embedding_distance`, `manipulation_check`, `make_pair_base`. |
| `generative_agents/reverie/backend_server/tests/test_persona_factory.py` | **Create.** Unit tests (offline; embeddings mocked). |
| `generative_agents/reverie/backend_server/tests/test_persona_factory_integration.py` | **Create.** Integration-gated: real embedding-distance monotonicity over δ. |

All commands run from `generative_agents/reverie/backend_server/`; `PY=../../../.venv/bin/python`.

---

### Task 1: Trait schema, deterministic midpoint, and `trait_distance`

**Files:**
- Create: `persona_factory.py`
- Test: `tests/test_persona_factory.py`

- [ ] **Step 1: Write the failing test** — create `tests/test_persona_factory.py`:
```python
import persona_factory as pf


def test_traits_constant_and_ordered():
    assert pf.TRAITS == ["warmth", "ambition", "dominance", "agreeableness",
                         "conscientiousness", "openness", "sociability", "volatility"]


def test_seed_midpoint_deterministic_and_in_range():
    a = pf.seed_midpoint("house-rivera")
    b = pf.seed_midpoint("house-rivera")
    assert a == b                                  # deterministic
    assert set(a.keys()) == set(pf.TRAITS)
    assert all(0.0 <= v <= 1.0 for v in a.values())
    assert pf.seed_midpoint("house-okafor") != a   # different seed -> different midpoint


def test_trait_distance():
    z = {t: 0.0 for t in pf.TRAITS}
    o = {t: 1.0 for t in pf.TRAITS}
    assert pf.trait_distance(z, z) == 0.0
    assert abs(pf.trait_distance(z, o) - 1.0) < 1e-9   # normalized by sqrt(8) -> max 1.0
```

- [ ] **Step 2: Run to verify it fails** — `$PY -m pytest tests/test_persona_factory.py -q` → FAIL (`ModuleNotFoundError: No module named 'persona_factory'`).

- [ ] **Step 3: Implement** — create `persona_factory.py`:
```python
"""persona_factory.py — generate same-house persona pairs at a controlled
identity distance delta (the experiment's IV). Deterministic per seed.
"""
import hashlib
import math

TRAITS = ["warmth", "ambition", "dominance", "agreeableness",
          "conscientiousness", "openness", "sociability", "volatility"]


def _hash_unit(seed_id, salt):
    """Deterministic float in [0,1) from (seed_id, salt) via SHA-256."""
    h = hashlib.sha256(f"{seed_id}|{salt}".encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


def seed_midpoint(seed_id):
    """A reproducible midpoint trait vector for this seed."""
    return {t: _hash_unit(seed_id, t) for t in TRAITS}


def trait_distance(a, b):
    """Euclidean distance over the 8-D trait vector, normalized by sqrt(8) to ~[0,1]."""
    sq = sum((a[t] - b[t]) ** 2 for t in TRAITS)
    return math.sqrt(sq) / math.sqrt(len(TRAITS))
```

- [ ] **Step 4: Run to verify it passes** — `$PY -m pytest tests/test_persona_factory.py -q` → PASS (3 passed).

- [ ] **Step 5: Commit**
```bash
cd /Users/mkrolick/Documents/GitHub/SmallDesire
git add -f generative_agents/reverie/backend_server/persona_factory.py
git add generative_agents/reverie/backend_server/tests/test_persona_factory.py
git commit -m "feat: persona trait schema + deterministic midpoint + trait_distance"
```

---

### Task 2: Symmetric δ-perturbation

**Files:**
- Modify: `persona_factory.py`
- Test: `tests/test_persona_factory.py`

- [ ] **Step 1: Write the failing test** — APPEND:
```python
def test_perturb_symmetric_and_delta_zero_identical():
    a0, b0 = pf.perturb("house-rivera", 0.0)
    assert a0 == b0                                  # delta=0 -> identical twins
    mid = pf.seed_midpoint("house-rivera")
    a, b = pf.perturb("house-rivera", 0.4)
    # symmetric around the midpoint: a+b == 2*mid on each trait (before clamping effects)
    for t in pf.TRAITS:
        assert abs((a[t] + b[t]) / 2 - mid[t]) < 1e-9 or a[t] in (0.0, 1.0) or b[t] in (0.0, 1.0)
    assert pf.trait_distance(a, b) > pf.trait_distance(a0, b0)   # bigger delta -> bigger distance


def test_perturb_deterministic():
    assert pf.perturb("house-rivera", 0.4) == pf.perturb("house-rivera", 0.4)


def test_perturb_distance_increases_with_delta():
    dists = [pf.trait_distance(*pf.perturb("house-okafor", d)) for d in (0.0, 0.2, 0.5, 0.9)]
    assert dists == sorted(dists)                     # monotonic non-decreasing
```

- [ ] **Step 2: Run to verify it fails** — `$PY -m pytest tests/test_persona_factory.py -k perturb -q` → FAIL (no attribute `perturb`).

- [ ] **Step 3: Implement** — add to `persona_factory.py`:
```python
def _unit_direction(seed_id):
    """A deterministic unit vector over the 8 traits (direction of perturbation)."""
    raw = [_hash_unit(seed_id, f"dir-{t}") - 0.5 for t in TRAITS]
    norm = math.sqrt(sum(x * x for x in raw)) or 1.0
    return [x / norm for x in raw]


def perturb(seed_id, delta):
    """Return two trait dicts placed symmetrically delta apart around the seed
    midpoint, along a deterministic direction. delta=0 -> identical. Clamped to [0,1]."""
    mid = seed_midpoint(seed_id)
    u = _unit_direction(seed_id)
    a, b = {}, {}
    for i, t in enumerate(TRAITS):
        a[t] = min(1.0, max(0.0, mid[t] + (delta / 2) * u[i]))
        b[t] = min(1.0, max(0.0, mid[t] - (delta / 2) * u[i]))
    return a, b
```

- [ ] **Step 4: Run to verify it passes** — `$PY -m pytest tests/test_persona_factory.py -k perturb -q` → PASS (3 passed). Then the whole file `$PY -m pytest tests/test_persona_factory.py -q`.

- [ ] **Step 5: Commit**
```bash
cd /Users/mkrolick/Documents/GitHub/SmallDesire
git add -f generative_agents/reverie/backend_server/persona_factory.py
git add generative_agents/reverie/backend_server/tests/test_persona_factory.py
git commit -m "feat: symmetric deterministic delta-perturbation of trait vectors"
```

---

### Task 3: Length-matched ISS rendering

**Files:**
- Modify: `persona_factory.py`
- Test: `tests/test_persona_factory.py`

- [ ] **Step 1: Write the failing test** — APPEND:
```python
ISS_KEYS = {"name", "first_name", "last_name", "age", "innate", "learned",
            "currently", "lifestyle", "living_area", "daily_plan_req"}


def test_render_iss_has_all_keys_and_name():
    a, b = pf.perturb("house-rivera", 0.4)
    iss = pf.render_iss(a, name="Ada Rivera", house="the Rivera household",
                        living_area="the Ville:Rivera household:main room",
                        vocation="barista")
    assert ISS_KEYS <= set(iss.keys())
    assert iss["name"] == "Ada Rivera"
    assert iss["first_name"] == "Ada" and iss["last_name"] == "Rivera"


def test_render_iss_length_matched():
    a, b = pf.perturb("house-rivera", 0.9)   # maximally different pair
    ctx = dict(house="the Rivera household",
               living_area="the Ville:Rivera household:main room", vocation="barista")
    ia = pf.render_iss(a, name="Ada Rivera", **ctx)
    ib = pf.render_iss(b, name="Bea Rivera", **ctx)
    # length-matched: the trait-driven fields have identical word counts across the pair
    for k in ("innate", "learned", "currently", "lifestyle"):
        assert len(ia[k].split()) == len(ib[k].split()), k


def test_render_iss_delta_zero_identical_except_name():
    a, b = pf.perturb("house-rivera", 0.0)
    ctx = dict(house="the Rivera household",
               living_area="the Ville:Rivera household:main room", vocation="barista")
    ia = pf.render_iss(a, name="Ada Rivera", **ctx)
    ib = pf.render_iss(b, name="Ada Rivera", **ctx)
    assert ia == ib   # identical traits + identical name+ctx -> identical ISS
```

- [ ] **Step 2: Run to verify it fails** — `$PY -m pytest tests/test_persona_factory.py -k render_iss -q` → FAIL (no attribute `render_iss`).

- [ ] **Step 3: Implement** — add to `persona_factory.py`:
```python
# 5-bucket adjective banks per trait (value -> exactly one word; keeps renders length-matched).
_BANKS = {
    "warmth":            ["cold", "distant", "even", "kind", "warm"],
    "ambition":          ["content", "easygoing", "steady", "driven", "relentless"],
    "dominance":         ["yielding", "deferential", "balanced", "assertive", "commanding"],
    "agreeableness":     ["combative", "skeptical", "fair", "agreeable", "accommodating"],
    "conscientiousness": ["careless", "casual", "orderly", "diligent", "meticulous"],
    "openness":          ["rigid", "conventional", "curious", "inventive", "visionary"],
    "sociability":       ["solitary", "private", "sociable", "gregarious", "magnetic"],
    "volatility":        ["serene", "calm", "measured", "tense", "volatile"],
}


def _adj(trait, value):
    bank = _BANKS[trait]
    idx = min(len(bank) - 1, int(value * len(bank)))
    return bank[idx]


def render_iss(traits, name, house, living_area, vocation):
    """Render a trait vector to the scratch ISS identity fields, length-matched
    (only single trait-derived words vary). Shared context fields are constant."""
    first, _, last = name.partition(" ")
    return {
        "name": name,
        "first_name": first,
        "last_name": last or first,
        "age": 28,
        "innate": ", ".join([_adj("warmth", traits["warmth"]),
                             _adj("dominance", traits["dominance"]),
                             _adj("agreeableness", traits["agreeableness"]),
                             _adj("volatility", traits["volatility"])]),
        "learned": (f"{first} grew up in {house} and works as a {vocation}; "
                    f"{first} is {_adj('ambition', traits['ambition'])} and "
                    f"{_adj('conscientiousness', traits['conscientiousness'])}."),
        "currently": (f"{first} is {_adj('openness', traits['openness'])} about new ideas "
                      f"and feels {_adj('volatility', traits['volatility'])} lately."),
        "lifestyle": (f"{first} is {_adj('sociability', traits['sociability'])}, "
                      f"sleeps around 11pm and wakes around 7am."),
        "living_area": living_area,
        "daily_plan_req": (f"{first} shares {house} with a housemate and spends the day "
                           f"around the Ville pursuing work as a {vocation}."),
    }
```

- [ ] **Step 4: Run to verify it passes** — `$PY -m pytest tests/test_persona_factory.py -k render_iss -q` → PASS (3 passed). Then run the whole file.

- [ ] **Step 5: Commit**
```bash
cd /Users/mkrolick/Documents/GitHub/SmallDesire
git add -f generative_agents/reverie/backend_server/persona_factory.py
git add generative_agents/reverie/backend_server/tests/test_persona_factory.py
git commit -m "feat: length-matched ISS rendering from trait vectors"
```

---

### Task 4: Embedding distance + manipulation check

**Files:**
- Modify: `persona_factory.py`
- Test: `tests/test_persona_factory.py`

- [ ] **Step 1: Write the failing test** — APPEND:
```python
def test_embedding_distance_and_manipulation_check(monkeypatch):
    # Deterministic fake embedding: hash text -> a small vector, so distance is computable offline.
    import hashlib

    def fake_embed(text):
        h = hashlib.sha256(text.encode()).digest()
        return [b / 255.0 for b in h[:6]]

    monkeypatch.setattr(pf.provider_client, "get_embedding", fake_embed)

    a, b = pf.perturb("house-rivera", 0.0)
    ctx = dict(house="the Rivera household",
               living_area="the Ville:Rivera household:main room", vocation="barista")
    ia = pf.render_iss(a, name="Ada Rivera", **ctx)
    ib = pf.render_iss(b, name="Ada Rivera", **ctx)
    assert pf.embedding_distance(ia, ib) == 0.0   # identical text -> 0 distance

    chk = pf.manipulation_check("house-rivera", 0.6,
                                name_a="Ada Rivera", name_b="Bea Rivera", **ctx)
    assert set(chk.keys()) >= {"designed_delta", "trait_distance", "embedding_distance"}
    assert chk["designed_delta"] == 0.6
    assert chk["trait_distance"] > 0.0
```

- [ ] **Step 2: Run to verify it fails** — `$PY -m pytest tests/test_persona_factory.py -k manipulation -q` → FAIL (no `embedding_distance`/`manipulation_check`, and/or no `provider_client` on the module).

- [ ] **Step 3: Implement** — add the import at the TOP of `persona_factory.py` (below the stdlib imports):
```python
from persona.prompt_template import provider_client
```
and add:
```python
def _iss_text(iss):
    """Flatten the trait-driven ISS fields into one string for embedding."""
    return " ".join(str(iss[k]) for k in ("innate", "learned", "currently", "lifestyle"))


def embedding_distance(iss_a, iss_b):
    """Cosine distance (1 - cos sim) between the two rendered personas' embeddings."""
    va = provider_client.get_embedding(_iss_text(iss_a))
    vb = provider_client.get_embedding(_iss_text(iss_b))
    dot = sum(x * y for x, y in zip(va, vb))
    na = math.sqrt(sum(x * x for x in va)) or 1.0
    nb = math.sqrt(sum(y * y for y in vb)) or 1.0
    return 1.0 - dot / (na * nb)


def manipulation_check(seed_id, delta, name_a, name_b, house, living_area, vocation):
    """Return designed delta, realized trait distance, and embedding distance for a pair."""
    a, b = perturb(seed_id, delta)
    ctx = dict(house=house, living_area=living_area, vocation=vocation)
    ia = render_iss(a, name=name_a, **ctx)
    ib = render_iss(b, name=name_b, **ctx)
    return {
        "designed_delta": delta,
        "trait_distance": trait_distance(a, b),
        "embedding_distance": embedding_distance(ia, ib),
    }
```

- [ ] **Step 4: Run to verify it passes** — `$PY -m pytest tests/test_persona_factory.py -k manipulation -q` → PASS. Then the whole file + confirm module import: `$PY -c "import persona_factory; print('ok')"`.

- [ ] **Step 5: Commit**
```bash
cd /Users/mkrolick/Documents/GitHub/SmallDesire
git add -f generative_agents/reverie/backend_server/persona_factory.py
git add generative_agents/reverie/backend_server/tests/test_persona_factory.py
git commit -m "feat: embedding distance + manipulation-check metrics"
```

---

### Task 5: Materialize a runnable 2-agent base for a (seed, δ) pair

**Files:**
- Modify: `persona_factory.py`
- Test: `tests/test_persona_factory.py`

- [ ] **Step 1: Write the failing test** — APPEND:
```python
def test_make_pair_base_writes_consistent_base():
    import json
    import os
    import shutil
    from utils import fs_storage

    out = "base_gen_test_pair"
    folder = f"{fs_storage}/{out}"
    shutil.rmtree(folder, ignore_errors=True)
    names = pf.make_pair_base("house-rivera", 0.0, out_name=out,
                              name_a="Ada Rivera", name_b="Bea Rivera")
    assert set(names) == {"Ada Rivera", "Bea Rivera"}
    meta = json.load(open(f"{folder}/reverie/meta.json"))
    assert set(meta["persona_names"]) == {"Ada Rivera", "Bea Rivera"}
    env = json.load(open(f"{folder}/environment/0.json"))
    assert set(env.keys()) == {"Ada Rivera", "Bea Rivera"}
    dirs = {d for d in os.listdir(f"{folder}/personas") if not d.startswith(".")}
    assert dirs == {"Ada Rivera", "Bea Rivera"}
    # the rendered identity made it into scratch.json
    sa = json.load(open(f"{folder}/personas/Ada Rivera/bootstrap_memory/scratch.json"))
    assert sa["name"] == "Ada Rivera" and "barista" in sa["learned"]
    # delta=0 -> identical innate traits between the two (identity twins)
    sb = json.load(open(f"{folder}/personas/Bea Rivera/bootstrap_memory/scratch.json"))
    assert sa["innate"] == sb["innate"]
    shutil.rmtree(folder, ignore_errors=True)
```

- [ ] **Step 2: Run to verify it fails** — `$PY -m pytest tests/test_persona_factory.py -k make_pair_base -q` → FAIL (no attribute `make_pair_base`).

- [ ] **Step 3: Implement** — add the imports at the TOP of `persona_factory.py`:
```python
import json
import os
import shutil

from utils import fs_storage
from global_methods import copyanything
```
and add (the template base `base_the_ville_isabella_maria` supplies the spatial memory, env positions, and meta structure; we rename its two personas to the generated ones and overwrite their identity fields):
```python
_TEMPLATE_BASE = "base_the_ville_isabella_maria"
_TEMPLATE_PERSONAS = ["Isabella Rodriguez", "Maria Lopez"]


def make_pair_base(seed_id, delta, out_name, name_a, name_b,
                   house=None, vocation="barista"):
    """Clone the template base into storage/<out_name> and overwrite its two
    personas with a generated (seed, delta) pair. Returns the two names."""
    house = house or f"the {name_a.split()[-1]} household"
    src = f"{fs_storage}/{_TEMPLATE_BASE}"
    dst = f"{fs_storage}/{out_name}"
    shutil.rmtree(dst, ignore_errors=True)
    copyanything(src, dst)

    a, b = perturb(seed_id, delta)
    pairs = [(name_a, a, _TEMPLATE_PERSONAS[0]), (name_b, b, _TEMPLATE_PERSONAS[1])]

    for new_name, traits, old_name in pairs:
        old_dir = f"{dst}/personas/{old_name}"
        new_dir = f"{dst}/personas/{new_name}"
        if old_dir != new_dir:
            os.rename(old_dir, new_dir)
        scratch_path = f"{new_dir}/bootstrap_memory/scratch.json"
        scratch = json.load(open(scratch_path))
        living_area = scratch.get("living_area") or "the Ville:artist's co-living space:common room"
        iss = render_iss(traits, name=new_name, house=house,
                         living_area=living_area, vocation=vocation)
        scratch.update(iss)
        scratch["act_event"] = [new_name, None, None]
        with open(scratch_path, "w") as f:
            json.dump(scratch, f, indent=2)

    # meta.json persona_names
    meta_path = f"{dst}/reverie/meta.json"
    meta = json.load(open(meta_path))
    meta["persona_names"] = [name_a, name_b]
    meta["fork_sim_code"] = out_name
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    # environment/0.json keys renamed (keep the template tile positions)
    env_path = f"{dst}/environment/0.json"
    env = json.load(open(env_path))
    remap = dict(zip(_TEMPLATE_PERSONAS, [name_a, name_b]))
    env = {remap.get(k, k): v for k, v in env.items()}
    with open(env_path, "w") as f:
        json.dump(env, f, indent=2)

    return [name_a, name_b]
```

- [ ] **Step 4: Run to verify it passes** — `$PY -m pytest tests/test_persona_factory.py -k make_pair_base -q` → PASS. Then the full suite `$PY -m pytest tests/ -q` → all pass + 2 skipped (the prior integration smokes). Note: generated `base_gen_*` folders match the `.gitignore` `base_*` keep-rule, but the test cleans up its folder, so nothing is committed.

- [ ] **Step 5: Commit**
```bash
cd /Users/mkrolick/Documents/GitHub/SmallDesire
git add -f generative_agents/reverie/backend_server/persona_factory.py
git add generative_agents/reverie/backend_server/tests/test_persona_factory.py
git commit -m "feat: materialize a runnable 2-agent base for a (seed, delta) pair"
```

---

### Task 6: Integration-gated live manipulation check (embeddings)

**Files:**
- Test: `tests/test_persona_factory_integration.py`

*(Uses REAL OpenAI embeddings — which are confirmed working even while TokensPLS chat is down — so this validates the IV manipulation end-to-end. Gated on `RUN_INTEGRATION`.)*

- [ ] **Step 1: Write the test** — create `tests/test_persona_factory_integration.py`:
```python
import os

import pytest

import persona_factory as pf


@pytest.mark.skipif(not os.environ.get("RUN_INTEGRATION"),
                    reason="set RUN_INTEGRATION=1 with EMBED_API_KEY set")
def test_embedding_distance_increases_with_delta():
    ctx = dict(house="the Rivera household",
               living_area="the Ville:Rivera household:main room", vocation="barista")
    dists = []
    for d in (0.0, 0.3, 0.6, 0.9):
        chk = pf.manipulation_check("house-rivera", d,
                                    name_a="Ada Rivera", name_b="Bea Rivera", **ctx)
        dists.append(chk["embedding_distance"])
    assert dists[0] == pytest.approx(0.0, abs=1e-6)     # delta=0 -> identical text -> 0 distance
    assert dists[-1] > dists[0]                          # bigger delta -> more separated embeddings
    # broadly monotonic: the largest delta is the most separated
    assert dists[-1] == max(dists)
```

- [ ] **Step 2: Confirm it collects + skips offline** — `$PY -m pytest tests/test_persona_factory_integration.py -v` → `1 skipped`.

- [ ] **Step 3: Full suite** — `$PY -m pytest tests/ -q` → all pass + 3 skipped.

- [ ] **Step 4: Commit**
```bash
cd /Users/mkrolick/Documents/GitHub/SmallDesire
git add generative_agents/reverie/backend_server/tests/test_persona_factory_integration.py
git commit -m "test: integration-gated live embedding-distance-vs-delta check"
```

---

## Self-Review

**Spec coverage (spec §3.1 identity manipulation):**
- Structured trait vectors, shared "house" seed → Tasks 1, 5. ✅
- Symmetric δ-perturbation around a midpoint → Task 2. ✅
- Length-matched render → Task 3. ✅
- Manipulation check (designed δ, embedding distance) → Tasks 4, 6. ✅
- The 5-level ladder, counterbalancing across seeds, and analysis are **experiment-runner concerns** (a later plan) — this plan provides the generator they call.

**Placeholder scan:** none — complete code, commands, expected output in every step.

**Type/name consistency:** `perturb(seed_id, delta) -> (a, b)`, `render_iss(traits, name, house, living_area, vocation)`, `trait_distance(a, b)`, `embedding_distance(iss_a, iss_b)`, `manipulation_check(seed_id, delta, name_a, name_b, house, living_area, vocation)`, `make_pair_base(seed_id, delta, out_name, name_a, name_b, ...)` are each defined once and called with matching signatures in later tasks. `provider_client.get_embedding` is the same seam used (and mocked) consistently.

---

## Execution Handoff

(filled in by the assistant after the plan is executed)
