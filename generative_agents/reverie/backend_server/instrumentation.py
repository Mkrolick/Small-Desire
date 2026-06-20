"""instrumentation.py — measurement logging for the SmallDesire experiment.

Captures the attitude/affect signals (relationship summaries, reflections about
the other agent, conversation transcripts) to per-run JSONL logs under
storage/<sim>/measurements/. Reads the agents' own memory/output; does NOT
modify the validated cognition.
"""
import json
import os

from utils import fs_storage


def _fmt_time(t):
    return t.strftime("%B %d, %Y, %H:%M:%S") if hasattr(t, "strftime") else str(t)


class MeasurementLog:
    """Appends newline-delimited JSON records to storage/<sim>/measurements/<kind>.jsonl."""

    def __init__(self, sim_code):
        self.dir = f"{fs_storage}/{sim_code}/measurements"
        os.makedirs(self.dir, exist_ok=True)

    def record(self, kind, step, curr_time, payload):
        rec = {"step": step, "curr_time": _fmt_time(curr_time), "kind": kind}
        rec.update(payload)
        with open(f"{self.dir}/{kind}.jsonl", "a") as f:
            f.write(json.dumps(rec) + "\n")
        return rec
