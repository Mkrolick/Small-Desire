import os

import pytest

import persona_factory as pf


@pytest.mark.skipif(not os.environ.get("RUN_INTEGRATION"),
                    reason="set RUN_INTEGRATION=1 with EMBED_API_KEY set")
def test_embedding_distance_increases_with_delta():
    """Name-invariant manipulation check: both personas rendered as 'Persona X'
    so embedding distance reflects trait-driven identity only.

    Delta ladder: (0.0, 0.15, 0.35, 0.6, 0.9).

    Assertions calibrated from a live run on 2026-06-19:
      house-rivera: [0.0, 0.0251, 0.074, 0.098, 0.1079]

    Note on coarse monotonicity: adjective buckets are discrete (5 values per
    trait), so small delta steps may not cross a bucket boundary and the
    per-step distance can be flat. We therefore assert only:
      1. delta=0 is exactly ~0 (name invariance; identical text -> identical embedding)
      2. The largest delta (0.9) produces a clearly positive, separating distance (> 0.02)
      3. dists[-1] >= dists[1]: the far end exceeds the first non-zero step
      4. dists[-1] == max(dists): the largest delta reaches the global maximum
         (holds for house-rivera in the calibration run; coarser seeds may not
         satisfy strict per-step monotonicity but do satisfy this endpoint claim)
    """
    ctx = dict(house="the Rivera household",
               living_area="the Ville:Rivera household:main room", vocation="barista")
    dists = []
    for d in (0.0, 0.15, 0.35, 0.6, 0.9):
        chk = pf.manipulation_check("house-rivera", d, **ctx)
        dists.append(chk["embedding_distance"])

    # (1) delta=0: identical text -> embedding distance is essentially zero
    assert dists[0] == pytest.approx(0.0, abs=1e-6)

    # (2) delta=0.9: clearly positive separation from the zero baseline
    assert dists[-1] > 0.02

    # (3) the far end exceeds the first non-zero step (weak monotonicity)
    assert dists[-1] >= dists[1]

    # (4) delta=0.9 achieves the global maximum distance across the ladder
    assert dists[-1] == max(dists)
