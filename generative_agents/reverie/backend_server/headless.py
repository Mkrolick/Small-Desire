"""Headless driver for a forked 2-agent sim — no Phaser frontend, no disk polling.

The Phaser frontend's only contribution each step is to echo the backend's
movement tile back as the next environment (sprite lands exactly on the tile),
so `next_env_from_movements` reproduces that handshake in-process.
"""
import json
import sys

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


if __name__ == "__main__":
    run_headless(sys.argv[1], sys.argv[2], int(sys.argv[3]))
