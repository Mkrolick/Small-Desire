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
