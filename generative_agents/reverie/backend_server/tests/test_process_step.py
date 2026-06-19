import datetime
import json
import os
import shutil

import reverie
from utils import fs_storage

NAMES = {"Isabella Rodriguez", "Maria Lopez"}


def test_process_step_writes_movement_and_advances(monkeypatch):
    sim = "test_process_step_unit"
    folder = f"{fs_storage}/{sim}"
    shutil.rmtree(folder, ignore_errors=True)
    rs = reverie.ReverieServer("base_the_ville_isabella_maria", sim)
    for p in rs.personas.values():
        monkeypatch.setattr(p, "move", lambda maze, personas, tile, t: ((1, 2), "S", "idle @ home"))
    env = json.load(open(f"{folder}/environment/0.json"))
    t0 = rs.curr_time
    movements = rs.process_step(env)
    assert set(movements["persona"].keys()) == NAMES
    saved = json.load(open(f"{folder}/movement/0.json"))
    assert saved["persona"]["Isabella Rodriguez"]["movement"] == [1, 2]
    assert saved["meta"]["curr_time"] == t0.strftime("%B %d, %Y, %H:%M:%S")
    assert rs.curr_time == t0 + datetime.timedelta(seconds=rs.sec_per_step)
    shutil.rmtree(folder, ignore_errors=True)


def test_process_step_carryover_across_two_steps(monkeypatch):
    sim = "test_process_step_carryover"
    folder = f"{fs_storage}/{sim}"
    shutil.rmtree(folder, ignore_errors=True)
    rs = reverie.ReverieServer("base_the_ville_isabella_maria", sim)
    for p in rs.personas.values():
        p.scratch.planned_path = []  # force the game-object cleanup branch to populate state
        monkeypatch.setattr(p, "move", lambda maze, personas, tile, t: ((3, 4), "S", "idle @ home"))
    env = json.load(open(f"{folder}/environment/0.json"))
    t0 = rs.curr_time

    m0 = rs.process_step(env)
    # after a step with empty planned_path, cleanup state is queued for the next step
    assert len(rs._game_obj_cleanup) >= 1
    env1 = {n: {"maze": "the_ville", "x": mv["movement"][0], "y": mv["movement"][1]}
            for n, mv in m0["persona"].items()}

    m1 = rs.process_step(env1)  # consumes the prior step's cleanup; must not error
    assert set(m1["persona"].keys()) == {"Isabella Rodriguez", "Maria Lopez"}
    assert os.path.exists(f"{folder}/movement/0.json")
    assert os.path.exists(f"{folder}/movement/1.json")
    assert rs.step == 2
    assert rs.curr_time == t0 + datetime.timedelta(seconds=2 * rs.sec_per_step)
    shutil.rmtree(folder, ignore_errors=True)
