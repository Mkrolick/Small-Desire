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
    assert dists[0] == pytest.approx(0.0, abs=1e-6)
    assert dists[-1] > dists[0]
    assert dists[-1] == max(dists)
