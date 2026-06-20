import json
import os
import shutil

import persona_factory as pf
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


def test_make_pair_base_with_dorm_template_is_copresent():
    out = "base_gen_copres_test"
    folder = f"{fs_storage}/{out}"
    shutil.rmtree(folder, ignore_errors=True)
    try:
        pf.make_pair_base("house-rivera", 0.4, out_name=out,
                          name_a="Ada Rivera", name_b="Bea Rivera",
                          template_base=pf.CO_PRESENCE_TEMPLATE,
                          template_personas=pf.CO_PRESENCE_PERSONAS)
        sectors = set()
        for nm in ("Ada Rivera", "Bea Rivera"):
            la = json.load(open(f"{folder}/personas/{nm}/bootstrap_memory/scratch.json"))["living_area"]
            sectors.add(la.split(":")[1])
        assert sectors == {"Dorm for Oak Hill College"}
    finally:
        shutil.rmtree(folder, ignore_errors=True)


def test_make_pair_base_rejects_mismatched_template_args():
    import pytest
    with pytest.raises(ValueError):
        pf.make_pair_base("seed", 0.3, out_name="base_gen_should_not_exist",
                          name_a="A B", name_b="C D",
                          template_base=pf.CO_PRESENCE_TEMPLATE)  # personas omitted -> error
