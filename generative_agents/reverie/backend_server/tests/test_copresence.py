import json
import os

from utils import fs_storage

DORM = f"{fs_storage}/base_the_ville_dorm_pair"
RESIDENTS = {"Maria Lopez", "Klaus Mueller"}


def test_dorm_pair_base_is_consistent_and_copresent():
    meta = json.load(open(f"{DORM}/reverie/meta.json"))
    assert set(meta["persona_names"]) == RESIDENTS
    env = json.load(open(f"{DORM}/environment/0.json"))
    assert set(env.keys()) == RESIDENTS
    dirs = {d for d in os.listdir(f"{DORM}/personas") if not d.startswith(".")}
    assert dirs == RESIDENTS
    sectors = set()
    for r in RESIDENTS:
        la = json.load(open(f"{DORM}/personas/{r}/bootstrap_memory/scratch.json"))["living_area"]
        sectors.add(la.split(":")[1])
    assert sectors == {"Dorm for Oak Hill College"}
