import json
import os
import shutil

import pytest

import headless
from utils import fs_storage

NAMES = ["Isabella Rodriguez", "Maria Lopez"]


@pytest.mark.skipif(not os.environ.get("RUN_INTEGRATION"),
                    reason="set RUN_INTEGRATION=1 with TokensPLS up + EMBED_API_KEY set")
def test_one_real_step_end_to_end():
    sim = "smoke_2agent"
    folder = f"{fs_storage}/{sim}"
    shutil.rmtree(folder, ignore_errors=True)
    headless.run_headless("base_the_ville_isabella_maria", sim, 1)
    mv = json.load(open(f"{folder}/movement/0.json"))
    for name in NAMES:
        assert name in mv["persona"]
        assert len(mv["persona"][name]["movement"]) == 2
        assert all(isinstance(c, int) for c in mv["persona"][name]["movement"])
    assert mv["meta"]["curr_time"] == "February 13, 2023, 00:00:10"
    shutil.rmtree(folder, ignore_errors=True)
