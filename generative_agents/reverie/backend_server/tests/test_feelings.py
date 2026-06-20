import types

import instrumentation as instr


def _fake_persona(name):
    scratch = types.SimpleNamespace(name=name)  # no get_str_iss -> defensive access yields ""
    return types.SimpleNamespace(scratch=scratch)


def test_parse_feeling_structured_and_fallback():
    assert instr._parse_feeling("SCORE: 6 | REASON: she keeps copying me") == (6, "she keeps copying me")
    score, reason = instr._parse_feeling("I'd say a 5 because it's tense")
    assert score == 5 and "tense" in reason
    s2, _ = instr._parse_feeling("On a 1 to 7 scale, SCORE: 7 | REASON: hostile")
    assert s2 == 7
    assert instr._parse_feeling("no number here")[0] is None
    # scale preamble must not be mistaken for the answer (fallback takes the last digit)
    assert instr._parse_feeling("between 1 and 7, I pick 6 — because envy")[0] == 6
    assert instr._parse_feeling("On a 1 to 7 scale, I feel 5")[0] == 5
    # out-of-range structured score -> no valid 1-7 score
    assert instr._parse_feeling("SCORE: 9 | REASON: out of range")[0] is None


def test_probe_feelings_logs_both_directions(monkeypatch):
    sim = "test_feelings_unit"
    log = instr.MeasurementLog(sim)
    monkeypatch.setattr(instr, "new_retrieve", lambda persona, fp, n_count=30: {fp[0]: []})
    calls = []
    def fake_chat(prompt, **kw):
        calls.append(prompt)
        return "SCORE: 4 | REASON: wary of them"
    monkeypatch.setattr(instr.provider_client, "chat_completion", fake_chat)

    personas = {"Ada Rivera": _fake_persona("Ada Rivera"), "Bea Rivera": _fake_persona("Bea Rivera")}
    instr.probe_feelings(personas, log, step=3, curr_time=__import__("datetime").datetime(2023, 2, 13, 0, 5, 0))

    path = f"{instr.fs_storage}/{sim}/measurements/feeling.jsonl"
    lines = [__import__("json").loads(l) for l in open(path)]
    assert len(lines) == 2
    assert {(l["from"], l["to"]) for l in lines} == {("Ada Rivera", "Bea Rivera"), ("Bea Rivera", "Ada Rivera")}
    assert all(l["score"] == 4 and "wary" in l["reason"] for l in lines)
    assert any("Ada Rivera" in p and "Bea Rivera" in p for p in calls)
    import shutil
    shutil.rmtree(f"{instr.fs_storage}/{sim}", ignore_errors=True)


def test_run_headless_instrumented_writes_feelings(monkeypatch):
    import shutil
    import reverie
    import headless
    sim = "test_feelings_run"
    folder = f"{instr.fs_storage}/{sim}"
    shutil.rmtree(folder, ignore_errors=True)

    monkeypatch.setattr(instr, "new_retrieve", lambda persona, fp, n_count=30: {fp[0]: []})
    monkeypatch.setattr(instr.converse, "generate_summarize_agent_relationship",
                        lambda a, b, retrieved: "summary")
    monkeypatch.setattr(instr.provider_client, "chat_completion",
                        lambda prompt, **kw: "SCORE: 5 | REASON: tense")
    monkeypatch.setattr(reverie.ReverieServer, "save", lambda self: None)
    orig_init = reverie.ReverieServer.__init__
    def patched_init(self, fork, sim_code):
        orig_init(self, fork, sim_code)
        for p in self.personas.values():
            monkeypatch.setattr(p, "move", lambda maze, personas, tile, t: ((1, 2), "S", "idle @ home"))
    monkeypatch.setattr(reverie.ReverieServer, "__init__", patched_init)

    headless.run_headless_instrumented("base_the_ville_isabella_maria", sim, 2, probe_every=1)
    feelings = [__import__("json").loads(l) for l in open(f"{folder}/measurements/feeling.jsonl")]
    assert len(feelings) == 4   # 2 ordered pairs x 2 steps
    assert all(f["score"] == 5 for f in feelings)
    shutil.rmtree(folder, ignore_errors=True)


def test_probe_feelings_survives_provider_hiccup(monkeypatch):
    # a TokensPLS hiccup mid-run must degrade to a null score, not crash the run
    sim = "test_feelings_hiccup"
    log = instr.MeasurementLog(sim)
    monkeypatch.setattr(instr, "new_retrieve", lambda persona, fp, n_count=30: {fp[0]: []})
    def boom(prompt, **kw):
        raise ConnectionError("TokensPLS down")
    monkeypatch.setattr(instr.provider_client, "chat_completion", boom)
    personas = {"Ada Rivera": _fake_persona("Ada Rivera"), "Bea Rivera": _fake_persona("Bea Rivera")}
    instr.probe_feelings(personas, log, step=1,
                         curr_time=__import__("datetime").datetime(2023, 2, 13, 0, 0, 0))
    import json, shutil
    lines = [json.loads(l) for l in open(f"{instr.fs_storage}/{sim}/measurements/feeling.jsonl")]
    assert len(lines) == 2 and all(l["score"] is None for l in lines)
    shutil.rmtree(f"{instr.fs_storage}/{sim}", ignore_errors=True)
