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


def capture_new_reflections(persona, other_personas, log, step, curr_time, cursor):
    """Log NEW thought nodes (those added since `cursor`) that reference another
    persona. seq_thought prepends newest at index 0, so the newest
    (len - cursor) entries are the new ones. Returns the updated cursor."""
    seq = persona.a_mem.seq_thought
    n_new = len(seq) - cursor
    if n_new <= 0:
        return len(seq)
    new_nodes = seq[:n_new]
    for node in new_nodes:
        text = " ".join([
            str(node.description), " ".join(node.keywords),
            str(node.subject), str(node.object),
        ]).lower()
        for other in other_personas:
            if other.scratch.first_name.lower() in text or other.scratch.name.lower() in text:
                log.record("reflection", step, curr_time, {
                    "persona": persona.scratch.name,
                    "about": other.scratch.name,
                    "description": node.description,
                    "poignancy": node.poignancy,
                    "keywords": list(node.keywords),
                    "evidence": list(node.filling),
                    "created": _fmt_time(node.created),
                })
                break
    return len(seq)


def capture_conversations(movements, log, step, curr_time):
    """Log each non-empty conversation transcript once (both participants share
    the same transcript object, so dedup by transcript content within the step)."""
    seen = set()
    persona_block = movements.get("persona", {})
    for name, m in persona_block.items():
        chat = m.get("chat")
        if not chat:
            continue
        key = json.dumps(chat, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        participants = [n for n, mm in persona_block.items()
                        if json.dumps(mm.get("chat"), sort_keys=True) == key]
        log.record("conversation", step, curr_time, {
            "participants": participants,
            "transcript": chat,
        })
