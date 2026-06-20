"""signatures.py — read the Girardian doubling signatures off the feeling-probe
trajectories. Plain trend math over the logged 1-7 scores; no LLM.
"""
import json

import numpy as np


def load_feelings(path):
    """Return {"<from>-><to>": [(step, score), ...]} for rows with a numeric score."""
    series = {}
    with open(path) as f:
        for line in f:
            r = json.loads(line)
            if r.get("score") is None:
                continue
            key = f'{r["from"]}->{r["to"]}'
            series.setdefault(key, []).append((int(r["step"]), float(r["score"])))
    for k in series:
        series[k].sort()
    return series


def escalation_slope(series):
    """Linear slope of score vs. step (>0 = hostility rising over time)."""
    if len(series) < 2:
        return 0.0
    steps = np.array([s for s, _ in series], dtype=float)
    scores = np.array([v for _, v in series], dtype=float)
    if np.ptp(steps) == 0:
        return 0.0
    return float(np.polyfit(steps, scores, 1)[0])


def _align(ab, ba):
    da, db = dict(ab), dict(ba)
    common = sorted(set(da) & set(db))
    return [da[s] for s in common], [db[s] for s in common]


def reciprocity(ab, ba):
    """Correlation of A->B and B->A score series aligned by step (mimesis of
    antagonism: each one's hostility tracks the other's). 0.0 if undefined."""
    xa, xb = _align(ab, ba)
    if len(xa) < 2 or np.std(xa) == 0 or np.std(xb) == 0:
        return 0.0
    return float(np.corrcoef(xa, xb)[0, 1])


def convergence(ab, ba):
    """Undifferentiation: how close the two directions' scores become by the end
    (1 / (1 + mean|A->B - B->A| over the last half)). Higher = more converged."""
    xa, xb = _align(ab, ba)
    if not xa:
        return 0.0
    half = xa[len(xa) // 2:], xb[len(xb) // 2:]
    diffs = [abs(a - b) for a, b in zip(*half)]
    return float(1.0 / (1.0 + (sum(diffs) / len(diffs)))) if diffs else 0.0


def compute_signatures(path):
    """Compute the signatures from a feeling.jsonl. Assumes a 2-agent pair."""
    series = load_feelings(path)
    keys = list(series.keys())
    escalation = {k: escalation_slope(series[k]) for k in keys}
    recip, conv = 0.0, 0.0
    if len(keys) == 2:
        recip = reciprocity(series[keys[0]], series[keys[1]])
        conv = convergence(series[keys[0]], series[keys[1]])
    return {"escalation": escalation, "reciprocity": recip, "convergence": conv}
