"""conversation_mirroring.py — turn-level mimetic mirroring INSIDE conversation
transcripts. This is the proper test of Girardian reciprocity, and the fix for
the confound in `signatures.reciprocity` (which scores nonzero even when agents
never speak): here, mirroring is measured only between actual conversational
turns, so it is correctly undefined when there is no interaction.

Per turn we score the speaker's emotional tone toward the other on -3 (hostile)
.. +3 (warm). Then per conversation:
  - mirroring  = correlation between each turn's valence and the OTHER speaker's
                 immediately prior turn (tone contagion / mimesis). High +ve =
                 each speaker mirrors the other's prior tone.
  - escalation = slope of valence over the turns (<0 = the exchange sours toward
                 hostility; >0 = it warms).
  - mean_valence = warm (+) vs hostile (-) overall.
Girardian *antagonistic* mimesis would be high mirroring + negative valence +
negative escalation. Pro-social mimesis is high mirroring + positive valence.
"""
import json
import os
import re

import numpy as np

from persona.prompt_template import provider_client


def _valence_prompt(transcript):
    lines = "\n".join(f"{i+1}. {spk}: {utt}" for i, (spk, utt) in enumerate(transcript))
    return (
        "Below is a conversation between two people. For EACH numbered turn, rate "
        "the speaker's emotional tone toward the other person on an integer scale "
        "from -3 (hostile, resentful, contemptuous) through 0 (neutral) to +3 "
        "(warm, friendly, affectionate).\n\n"
        f"{lines}\n\n"
        "Respond with ONLY one line, a comma-separated list of integers — one per "
        "turn, in order — prefixed exactly like this:\n"
        "VALENCES: 2, 1, -1, 0"
    )


def score_turn_valences(transcript):
    """Per-turn valence (-3..+3) via the LLM, aligned to `transcript`
    (None for any turn we couldn't score). Survives a provider hiccup."""
    if not transcript:
        return []
    try:
        resp = provider_client.chat_completion(_valence_prompt(transcript))
    except Exception:
        return [None] * len(transcript)
    m = re.search(r"VALENCES?:\s*([^\n]+)", resp, re.IGNORECASE)
    text = m.group(1) if m else resp
    vals = [v for v in (int(n) for n in re.findall(r"-?\d+", text)) if -3 <= v <= 3]
    out = vals[:len(transcript)]
    out += [None] * (len(transcript) - len(out))
    return out


def mirroring_stats(valences, speakers):
    """Turn-level mirroring + escalation for one conversation.
    `valences[i]` may be None (dropped); `speakers[i]` is the turn's speaker.

    `mirroring` is the BASELINE-CONTROLLED measure (each turn demeaned by its own
    speaker's average tone) — it answers "when the other deviated warm/cold from
    their usual, did this speaker deviate the same way?", the actual test of
    mimesis. `mirroring_raw` keeps the un-demeaned version, which is confounded by
    a constant warmth gap between the two speakers (alternating turns then look
    anti-correlated even with zero mutual influence)."""
    sums, counts = {}, {}
    for v, s in zip(valences, speakers):
        if v is not None:
            sums[s] = sums.get(s, 0) + v
            counts[s] = counts.get(s, 0) + 1
    base = {s: sums[s] / counts[s] for s in counts}
    prev, cur, dprev, dcur = [], [], [], []
    for i in range(1, len(valences)):
        if (speakers[i] != speakers[i - 1]
                and valences[i] is not None and valences[i - 1] is not None):
            prev.append(valences[i - 1])
            cur.append(valences[i])
            dprev.append(valences[i - 1] - base[speakers[i - 1]])
            dcur.append(valences[i] - base[speakers[i]])

    def _corr(x, y):
        if len(x) >= 2 and np.std(x) > 1e-9 and np.std(y) > 1e-9:
            return float(np.corrcoef(x, y)[0, 1])
        return None

    idx = [i for i, v in enumerate(valences) if v is not None]
    vv = [valences[i] for i in idx]
    escalation = float(np.polyfit(idx, vv, 1)[0]) if len(vv) >= 2 and np.ptp(idx) > 0 else 0.0
    return {"mirroring": _corr(dprev, dcur),
            "mirroring_raw": _corr(prev, cur),
            "escalation": escalation,
            "mean_valence": float(np.mean(vv)) if vv else None,
            "n_turns": len(vv)}


def analyze_run(run_path, max_convos=None):
    """Score every conversation in `run_path`/measurements/conversation.jsonl and
    aggregate turn-level mirroring / escalation / valence across them."""
    p = f"{run_path}/measurements/conversation.jsonl"
    if not os.path.exists(p):
        return {"n_convos": 0, "n_scored": 0, "mean_mirroring": None,
                "mean_escalation": None, "mean_valence": None, "frac_souring": None}
    convos = [json.loads(l) for l in open(p)]
    if max_convos:
        convos = convos[:max_convos]
    per = []
    for c in convos:
        t = c.get("transcript") or []
        if len(t) < 3:
            continue
        per.append(mirroring_stats(score_turn_valences(t), [turn[0] for turn in t]))
    mir = [s["mirroring"] for s in per if s["mirroring"] is not None]
    mir_raw = [s["mirroring_raw"] for s in per if s["mirroring_raw"] is not None]
    esc = [s["escalation"] for s in per]
    mv = [s["mean_valence"] for s in per if s["mean_valence"] is not None]
    return {"n_convos": len(convos), "n_scored": len(per),
            "mean_mirroring": float(np.mean(mir)) if mir else None,
            "mean_mirroring_raw": float(np.mean(mir_raw)) if mir_raw else None,
            "mean_escalation": float(np.mean(esc)) if esc else None,
            "mean_valence": float(np.mean(mv)) if mv else None,
            "frac_souring": float(np.mean([e < 0 for e in esc])) if esc else None}
