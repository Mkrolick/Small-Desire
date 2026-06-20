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


def test_perturb_symmetric_and_delta_zero_identical():
    a0, b0 = pf.perturb("house-rivera", 0.0)
    assert a0 == b0
    mid = pf.seed_midpoint("house-rivera")
    a, b = pf.perturb("house-rivera", 0.4)
    for t in pf.TRAITS:
        assert abs((a[t] + b[t]) / 2 - mid[t]) < 1e-9 or a[t] in (0.0, 1.0) or b[t] in (0.0, 1.0)
    assert pf.trait_distance(a, b) > pf.trait_distance(a0, b0)


def test_perturb_deterministic():
    assert pf.perturb("house-rivera", 0.4) == pf.perturb("house-rivera", 0.4)


def test_perturb_distance_increases_with_delta():
    dists = [pf.trait_distance(*pf.perturb("house-okafor", d)) for d in (0.0, 0.2, 0.5, 0.9)]
    assert dists == sorted(dists)
