import json
import os
import shutil

import pytest

import headless
from utils import fs_storage


@pytest.mark.skipif(not os.environ.get("RUN_INTEGRATION"),
                    reason="set RUN_INTEGRATION=1 with TokensPLS up + EMBED_API_KEY set")
def test_instrumented_run_writes_relationship_log():
    sim = "smoke_instrumented"
    folder = f"{fs_storage}/{sim}"
    shutil.rmtree(folder, ignore_errors=True)
    headless.run_headless_instrumented("base_the_ville_isabella_maria", sim, 1, probe_every=1)
    rel_path = f"{folder}/measurements/relationship_summary.jsonl"
    assert os.path.exists(rel_path)
    lines = [json.loads(l) for l in open(rel_path)]
    assert len(lines) == 2
    for r in lines:
        assert r["source"] == "probe"
        assert isinstance(r["summary"], str) and r["summary"].strip()
        assert (r["from"], r["to"]) in {
            ("Isabella Rodriguez", "Maria Lopez"), ("Maria Lopez", "Isabella Rodriguez")}
    shutil.rmtree(folder, ignore_errors=True)
