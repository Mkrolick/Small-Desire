import json

import signatures as sg


def _write_feelings(tmp_path, rows):
    p = tmp_path / "feeling.jsonl"
    with open(p, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    return str(p)


def test_escalation_slope_positive_when_rising():
    series = [(0, 2), (1, 3), (2, 4), (3, 6)]
    assert sg.escalation_slope(series) > 0.9


def test_reciprocity_high_when_mirrored():
    ab = [(0, 2), (1, 3), (2, 5)]
    ba = [(0, 2), (1, 4), (2, 6)]
    assert sg.reciprocity(ab, ba) > 0.9


def test_compute_signatures_from_feeling_log(tmp_path):
    rows = []
    for step, (s_ab, s_ba) in enumerate([(2, 2), (3, 4), (5, 5), (6, 6)]):
        rows.append({"step": step, "from": "Ada Rivera", "to": "Bea Rivera", "score": s_ab})
        rows.append({"step": step, "from": "Bea Rivera", "to": "Ada Rivera", "score": s_ba})
    path = _write_feelings(tmp_path, rows)
    out = sg.compute_signatures(path)
    assert out["escalation"]["Ada Rivera->Bea Rivera"] > 0
    assert out["reciprocity"] > 0.5
    assert "convergence" in out


def test_load_feelings_drops_unparsed_scores(tmp_path):
    rows = [{"step": 0, "from": "A", "to": "B", "score": None},
            {"step": 1, "from": "A", "to": "B", "score": 3}]
    path = _write_feelings(tmp_path, rows)
    series = sg.load_feelings(path)["A->B"]
    assert series == [(1, 3)]
