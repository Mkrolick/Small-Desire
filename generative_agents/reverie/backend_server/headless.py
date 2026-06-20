"""Headless driver for a forked 2-agent sim — no Phaser frontend, no disk polling.

The Phaser frontend's only contribution each step is to echo the backend's
movement tile back as the next environment (sprite lands exactly on the tile),
so `next_env_from_movements` reproduces that handshake in-process.
"""
import json
import sys

import instrumentation
from reverie import ReverieServer
from utils import fs_storage


def next_env_from_movements(movements):
    """The feeder: next environment = each persona's just-written movement tile."""
    env = {}
    for name, m in movements["persona"].items():
        x, y = m["movement"]
        env[name] = {"maze": "the_ville", "x": x, "y": y}
    return env


def run_headless(fork_sim_code, sim_code, n_steps):
    """Fork `fork_sim_code` into `sim_code`, run `n_steps`, save. Returns the server."""
    rs = ReverieServer(fork_sim_code, sim_code)
    sim_folder = f"{fs_storage}/{sim_code}"
    # ReverieServer.__init__ already read environment/<step>.json to place personas
    # at their initial tiles; process_step needs that same full env dict (not just the
    # extracted positions), so we re-read it for the first step. (No off-by-one: rs.step
    # is still the initial step here.)
    with open(f"{sim_folder}/environment/{rs.step}.json") as f:
        env = json.load(f)
    for _ in range(n_steps):
        movements = rs.process_step(env)
        env = next_env_from_movements(movements)
    rs.save()
    return rs


def run_headless_instrumented(fork_sim_code, sim_code, n_steps, probe_every=1):
    """Like run_headless, but captures measurements each step:
      - new reflection thoughts about the other agent,
      - conversation transcripts,
      - (every `probe_every` steps) an on-demand relationship summary per ordered pair.
    Set probe_every=0 to disable the on-demand probe. Returns the server."""
    rs = ReverieServer(fork_sim_code, sim_code)
    log = instrumentation.MeasurementLog(sim_code)
    cursors = {name: 0 for name in rs.personas}
    sim_folder = f"{fs_storage}/{sim_code}"
    # ReverieServer.__init__ already read environment/<step>.json to place personas;
    # process_step needs that same full env dict, so we re-read it for the first step.
    with open(f"{sim_folder}/environment/{rs.step}.json") as f:
        env = json.load(f)
    for i in range(n_steps):
        step = rs.step            # the step being processed (process_step increments it)
        step_time = rs.curr_time  # that step's timestamp (process_step advances it); matches movement/<step>.json
        movements = rs.process_step(env)
        for name, persona in rs.personas.items():
            others = [p for n, p in rs.personas.items() if n != name]
            cursors[name] = instrumentation.capture_new_reflections(
                persona, others, log, step, step_time, cursors[name])
        instrumentation.capture_conversations(movements, log, step, step_time)
        if probe_every and (i % probe_every == 0):
            instrumentation.probe_relationships(rs.personas, log, step, step_time)
        env = next_env_from_movements(movements)
    rs.save()
    return rs


if __name__ == "__main__":
    run_headless(sys.argv[1], sys.argv[2], int(sys.argv[3]))
