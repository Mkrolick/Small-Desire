import json
import os
import shutil

import pytest

import headless
import persona_factory as pf
from utils import fs_storage


@pytest.mark.skipif(not os.environ.get("RUN_INTEGRATION"),
                    reason="set RUN_INTEGRATION=1 with TokensPLS up + EMBED_API_KEY set")
def test_copresent_pair_runs_and_logs():
    sim = "smoke_copresence"
    folder = f"{fs_storage}/{sim}"
    run_folder = f"{fs_storage}/{sim}_run"
    shutil.rmtree(folder, ignore_errors=True)
    shutil.rmtree(run_folder, ignore_errors=True)
    try:
        pf.make_copresent_pair("house-rivera", 0.0, out_name=sim,
                               name_a="Ada Rivera", name_b="Bea Rivera")
        assert pf.same_house(folder) is True
        headless.run_headless_instrumented(sim, f"{sim}_run", 2, probe_every=1)
        rel = f"{run_folder}/measurements/relationship_summary.jsonl"
        assert os.path.exists(rel)
        lines = [json.loads(l) for l in open(rel)]
        assert len(lines) >= 2     # both ordered-pair probes, at least one step
        convo_path = f"{run_folder}/measurements/conversation.jsonl"
        n_convos = len(open(convo_path).read().splitlines()) if os.path.exists(convo_path) else 0
        print(f"co-presence run: {len(lines)} relationship probes, {n_convos} conversations captured")
    finally:
        shutil.rmtree(folder, ignore_errors=True)
        shutil.rmtree(run_folder, ignore_errors=True)
