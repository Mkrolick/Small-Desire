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
