"""persona_factory.py — generate same-house persona pairs at a controlled
identity distance delta (the experiment's IV). Deterministic per seed.
"""
import hashlib
import math

from persona.prompt_template import provider_client

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


def _iss_text(iss):
    """Flatten the trait-driven ISS fields into one string for embedding."""
    return " ".join(str(iss[k]) for k in ("innate", "learned", "currently", "lifestyle"))


def embedding_distance(iss_a, iss_b):
    """Cosine distance (1 - cos sim) between the two rendered personas' embeddings.
    Clamped to [0.0, 1.0] to absorb floating-point rounding for identical inputs."""
    va = provider_client.get_embedding(_iss_text(iss_a))
    vb = provider_client.get_embedding(_iss_text(iss_b))
    dot = sum(x * y for x, y in zip(va, vb))
    na = math.sqrt(sum(x * x for x in va)) or 1.0
    nb = math.sqrt(sum(y * y for y in vb)) or 1.0
    return max(0.0, 1.0 - dot / (na * nb))


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
