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
    a, b = pf.perturb("house-rivera", 0.9)
    ctx = dict(house="the Rivera household",
               living_area="the Ville:Rivera household:main room", vocation="barista")
    ia = pf.render_iss(a, name="Ada Rivera", **ctx)
    ib = pf.render_iss(b, name="Bea Rivera", **ctx)
    for k in ("innate", "learned", "currently", "lifestyle"):
        assert len(ia[k].split()) == len(ib[k].split()), k


def test_render_iss_delta_zero_identical_except_name():
    a, b = pf.perturb("house-rivera", 0.0)
    ctx = dict(house="the Rivera household",
               living_area="the Ville:Rivera household:main room", vocation="barista")
    ia = pf.render_iss(a, name="Ada Rivera", **ctx)
    ib = pf.render_iss(b, name="Ada Rivera", **ctx)
    assert ia == ib
