import persona_factory as pf


def test_traits_constant_and_ordered():
    assert pf.TRAITS == ["warmth", "ambition", "dominance", "agreeableness",
                         "conscientiousness", "openness", "sociability", "volatility"]


def test_seed_midpoint_deterministic_and_in_range():
    a = pf.seed_midpoint("house-rivera")
    b = pf.seed_midpoint("house-rivera")
    assert a == b
    assert set(a.keys()) == set(pf.TRAITS)
    assert all(0.0 <= v <= 1.0 for v in a.values())
    assert pf.seed_midpoint("house-okafor") != a


def test_trait_distance():
    z = {t: 0.0 for t in pf.TRAITS}
    o = {t: 1.0 for t in pf.TRAITS}
    assert pf.trait_distance(z, z) == 0.0
    assert abs(pf.trait_distance(z, o) - 1.0) < 1e-9
