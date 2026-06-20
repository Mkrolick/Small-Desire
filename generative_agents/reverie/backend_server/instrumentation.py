"""instrumentation.py — measurement logging for the SmallDesire experiment.

Captures the attitude/affect signals (relationship summaries, reflections about
the other agent, conversation transcripts) to per-run JSONL logs under
storage/<sim>/measurements/. Reads the agents' own memory/output; does NOT
modify the validated cognition.
"""
import json
import os
import re

from utils import fs_storage
from persona.cognitive_modules import converse
from persona.cognitive_modules.retrieve import new_retrieve
from persona.prompt_template import provider_client


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


def _persona_iss(persona):
    """The persona's identity block if available (real personas have get_str_iss).
    Returns empty string if unavailable or if the scratch state is incomplete
    (e.g. curr_time not yet set before first move)."""
    getter = getattr(persona.scratch, "get_str_iss", None)
    if not callable(getter):
        return ""
    try:
        return getter()
    except Exception:
        return ""


def _parse_feeling(text):
    """Extract a 1-7 score and reason from a feeling response (gpt-5.4-safe).
    Prefers the explicit 'SCORE: n | REASON: ...' format; falls back to the LAST
    standalone 1-7 digit (the answer usually follows any restated scale).
    Returns (score|None, reason)."""
    m = re.search(r"SCORE:\s*([1-7])", text, re.IGNORECASE)
    if m:
        score = int(m.group(1))
    else:
        digits = re.findall(r"\b([1-7])\b", text)
        score = int(digits[-1]) if digits else None
    rm = re.search(r"REASON:\s*(.+)", text, re.IGNORECASE | re.DOTALL)
    reason = (rm.group(1) if rm else text).strip()
    return score, reason


def probe_feelings(personas, log, step, curr_time, n_retrieve=30):
    """Ask each agent, in character, how warm vs. hostile it feels toward the other
    (1=warm .. 7=hostile) + why, via an LLM call. Logs a 'feeling' record per
    ordered pair. This is the primary DV: the agent's self-reported attitude."""
    names = list(personas.keys())
    for a_name in names:
        for b_name in names:
            if a_name == b_name:
                continue
            a, b = personas[a_name], personas[b_name]
            retrieved = new_retrieve(a, [b.scratch.name], n_retrieve)
            context = "\n".join(node.embedding_key for nodes in retrieved.values() for node in nodes)
            prompt = (
                f"You are {a.scratch.name}. {_persona_iss(a)}\n"
                f"Here is what you know and remember about {b.scratch.name}:\n{context}\n\n"
                f"On a scale of 1 to 7, where 1 means warm and friendly and 7 means hostile "
                f"and resentful, how do you genuinely feel about {b.scratch.name} right now?\n"
                f"Respond in exactly this format and nothing else:\n"
                f"SCORE: <a single number 1-7> | REASON: <one short sentence>"
            )
            resp = provider_client.chat_completion(prompt)
            score, reason = _parse_feeling(resp)
            log.record("feeling", step, curr_time, {
                "from": a_name, "to": b_name, "score": score, "reason": reason, "raw": resp,
            })


def probe_relationships(personas, log, step, curr_time, n_retrieve=50):
    """On-demand attitude DV: for each ordered pair (A,B), retrieve A's memories
    about B and compute A's relationship summary, logging it with source='probe'.
    This is the dense longitudinal signal (independent of whether they conversed)."""
    names = list(personas.keys())
    for a_name in names:
        for b_name in names:
            if a_name == b_name:
                continue
            a, b = personas[a_name], personas[b_name]
            retrieved = new_retrieve(a, [b.scratch.name], n_retrieve)
            summary = converse.generate_summarize_agent_relationship(a, b, retrieved)
            log.record("relationship_summary", step, curr_time, {
                "from": a_name, "to": b_name, "summary": summary, "source": "probe",
            })
