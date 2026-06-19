import json
import os

BASE = "../../environment/frontend_server/storage/base_the_ville_isabella_maria"
EXPECTED = {"Isabella Rodriguez", "Maria Lopez"}


def test_two_agent_base_is_consistent():
    meta = json.load(open(f"{BASE}/reverie/meta.json"))
    names = set(meta["persona_names"])
    env = json.load(open(f"{BASE}/environment/0.json"))
    dirs = {d for d in os.listdir(f"{BASE}/personas") if not d.startswith(".")}
    assert names == EXPECTED
    assert set(env.keys()) == EXPECTED
    assert dirs == EXPECTED
