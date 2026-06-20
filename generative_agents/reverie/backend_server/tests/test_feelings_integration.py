import json
import os
import shutil

import pytest

import headless
import persona_factory as pf
from utils import fs_storage


@pytest.mark.skipif(not os.environ.get("RUN_INTEGRATION"),
                    reason="set RUN_INTEGRATION=1 with TokensPLS up + EMBED_API_KEY set")
def test_feeling_probe_writes_scores_live():
    sim = "smoke_feelings"
    folder = f"{fs_storage}/{sim}"
    run = f"{fs_storage}/{sim}_run"
    shutil.rmtree(folder, ignore_errors=True)
    shutil.rmtree(run, ignore_errors=True)
    try:
        pf.make_copresent_pair("house-rivera", 0.9, out_name=sim,
                               name_a="Ada Rivera", name_b="Bea Rivera")
        headless.run_headless_instrumented(sim, f"{sim}_run", 1, probe_every=1)
        feels = [json.loads(l) for l in open(f"{run}/measurements/feeling.jsonl")]
        assert len(feels) == 2
        for f in feels:
            assert f["score"] in range(1, 8)
            assert isinstance(f["reason"], str) and f["reason"].strip()
        print("live feelings:", [(f["from"], f["to"], f["score"]) for f in feels])
    finally:
        shutil.rmtree(folder, ignore_errors=True)
        shutil.rmtree(run, ignore_errors=True)
