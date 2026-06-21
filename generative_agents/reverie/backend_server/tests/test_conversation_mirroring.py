import json

import conversation_mirroring as cm


def test_score_turn_valences_parses_list(monkeypatch):
    monkeypatch.setattr(cm.provider_client, "chat_completion",
                        lambda prompt, **kw: "VALENCES: 2, 1, -1, 0")
    t = [["A", "hi"], ["B", "hey"], ["A", "ugh"], ["B", "ok"]]
    assert cm.score_turn_valences(t) == [2, 1, -1, 0]


def test_score_turn_valences_robust_to_prose_and_turn_numbers(monkeypatch):
    # model echoes turn numbers / prose; only the VALENCES line should count, clamped to -3..3
    monkeypatch.setattr(cm.provider_client, "chat_completion",
                        lambda prompt, **kw: "Here are my ratings.\nVALENCES: 3, 3, 2")
    assert cm.score_turn_valences([["A", "x"], ["B", "y"], ["A", "z"]]) == [3, 3, 2]


def test_score_turn_valences_pads_and_survives_hiccup(monkeypatch):
    def boom(prompt, **kw):
        raise ConnectionError("down")
    monkeypatch.setattr(cm.provider_client, "chat_completion", boom)
    out = cm.score_turn_valences([["A", "x"], ["B", "y"]])
    assert out == [None, None]


def test_mirroring_high_when_tone_is_contagious():
    # consecutive (cross-speaker) turns track each other -> high positive mirroring
    vals = [3, 2, 2, 1, 1, 0, 0, -1]
    spk = ["A", "B", "A", "B", "A", "B", "A", "B"]
    s = cm.mirroring_stats(vals, spk)
    assert s["mirroring"] > 0.85          # strongly contagious tone across speakers
    assert s["escalation"] < 0          # tone declines over the turns (souring)
    assert s["n_turns"] == 8


def test_baseline_difference_is_not_mimesis():
    # A always warm (+2), B always cool (-2): constant tones, zero mutual influence.
    # Raw lag-1 looks strongly negative (alternation artifact); demeaned is correctly
    # undefined (no within-speaker variation to mirror).
    vals = [2, -2, 2, -2, 2, -2]
    spk = ["A", "B", "A", "B", "A", "B"]
    s = cm.mirroring_stats(vals, spk)
    assert s["mirroring_raw"] < -0.9      # the confound my v1 metric fell for
    assert s["mirroring"] is None         # baseline-controlled: no real mimesis


def test_mirroring_none_when_no_cross_speaker_pairs():
    s = cm.mirroring_stats([1, 2], ["A", "A"])   # same speaker only
    assert s["mirroring"] is None


def test_mirroring_drops_none_valences():
    vals = [2, None, 2, 1]
    spk = ["A", "B", "A", "B"]
    s = cm.mirroring_stats(vals, spk)
    assert s["n_turns"] == 3            # the None turn is excluded


def test_analyze_run_aggregates(tmp_path, monkeypatch):
    md = tmp_path / "measurements"
    md.mkdir()
    rows = [
        {"participants": ["A", "B"], "transcript": [["A", "hi"], ["B", "hey"], ["A", "nice"], ["B", "yes"]]},
        {"participants": ["A", "B"], "transcript": [["A", "ok"], ["B", "sure"], ["A", "fine"], ["B", "good"]]},
    ]
    with open(md / "conversation.jsonl", "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    monkeypatch.setattr(cm.provider_client, "chat_completion",
                        lambda prompt, **kw: "VALENCES: 2, 2, 3, 3")
    out = cm.analyze_run(str(tmp_path))
    assert out["n_convos"] == 2 and out["n_scored"] == 2
    assert out["mean_valence"] > 0          # warm
    assert out["mean_mirroring"] is not None


def test_analyze_run_no_conversations(tmp_path):
    (tmp_path / "measurements").mkdir()
    out = cm.analyze_run(str(tmp_path))
    assert out["n_convos"] == 0 and out["mean_mirroring"] is None
