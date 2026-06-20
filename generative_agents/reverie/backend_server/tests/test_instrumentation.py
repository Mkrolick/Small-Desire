import datetime
import json

import instrumentation
from utils import fs_storage


def test_measurement_log_writes_jsonl(tmp_path, monkeypatch):
    sim = "test_measlog_unit"
    log = instrumentation.MeasurementLog(sim)
    t = datetime.datetime(2023, 2, 13, 0, 0, 10)
    rec = log.record("relationship_summary", 3, t, {"from": "A", "to": "B", "summary": "wary"})
    path = f"{fs_storage}/{sim}/measurements/relationship_summary.jsonl"
    line = open(path).read().strip()
    parsed = json.loads(line)
    assert parsed["step"] == 3
    assert parsed["kind"] == "relationship_summary"
    assert parsed["curr_time"] == "February 13, 2023, 00:00:10"
    assert parsed["from"] == "A" and parsed["to"] == "B" and parsed["summary"] == "wary"
    assert rec == parsed
    import shutil
    shutil.rmtree(f"{fs_storage}/{sim}", ignore_errors=True)


import types

import datetime as _dt


def _fake_node(description, keywords, subject="", obj="", poignancy=5, filling=None):
    return types.SimpleNamespace(
        description=description, keywords=set(keywords), subject=subject, object=obj,
        poignancy=poignancy, filling=filling or [], created=_dt.datetime(2023, 2, 13, 0, 1, 0),
    )


def _fake_persona(name, first_name, seq_thought):
    scratch = types.SimpleNamespace(name=name, first_name=first_name)
    a_mem = types.SimpleNamespace(seq_thought=list(seq_thought))
    return types.SimpleNamespace(scratch=scratch, a_mem=a_mem)


def test_capture_new_reflections_logs_only_partner_refs(monkeypatch):
    sim = "test_capture_refl_unit"
    log = instrumentation.MeasurementLog(sim)
    maria = _fake_persona("Maria Lopez", "Maria", [])
    isabella = _fake_persona("Isabella Rodriguez", "Isabella", [])
    isabella.a_mem.seq_thought = [
        _fake_node("Isabella finds Maria competitive", ["Maria", "competitive"], "Isabella", "Maria", 8),
        _fake_node("Isabella likes coffee", ["coffee"], "Isabella", "coffee", 2),
    ]
    cursor = instrumentation.capture_new_reflections(
        isabella, [maria], log, step=2, curr_time=_dt.datetime(2023, 2, 13, 0, 1, 0), cursor=0)
    assert cursor == 2
    path = f"{instrumentation.fs_storage}/{sim}/measurements/reflection.jsonl"
    lines = [__import__("json").loads(l) for l in open(path)]
    assert len(lines) == 1
    r = lines[0]
    assert r["persona"] == "Isabella Rodriguez" and r["about"] == "Maria Lopez"
    assert r["poignancy"] == 8 and "Maria" in r["description"]
    import shutil
    shutil.rmtree(f"{instrumentation.fs_storage}/{sim}", ignore_errors=True)


def test_capture_new_reflections_respects_cursor(monkeypatch):
    sim = "test_capture_refl_cursor"
    log = instrumentation.MeasurementLog(sim)
    maria = _fake_persona("Maria Lopez", "Maria", [])
    isabella = _fake_persona("Isabella Rodriguez", "Isabella", [
        _fake_node("old thought about Maria", ["Maria"], "Isabella", "Maria", 5),
    ])
    cursor = instrumentation.capture_new_reflections(
        isabella, [maria], log, step=5, curr_time=_dt.datetime(2023, 2, 13, 0, 5, 0), cursor=1)
    assert cursor == 1
    path = f"{instrumentation.fs_storage}/{sim}/measurements/reflection.jsonl"
    import os
    assert not os.path.exists(path)
    import shutil
    shutil.rmtree(f"{instrumentation.fs_storage}/{sim}", ignore_errors=True)


def test_capture_conversations_logs_unique_transcripts():
    sim = "test_capture_convo_unit"
    log = instrumentation.MeasurementLog(sim)
    convo = [["Isabella", "Hi Maria"], ["Maria", "Hi Isabella"]]
    movements = {"persona": {
        "Isabella Rodriguez": {"movement": [1, 2], "chat": convo},
        "Maria Lopez": {"movement": [3, 4], "chat": convo},
    }, "meta": {}}
    instrumentation.capture_conversations(
        movements, log, step=4, curr_time=__import__("datetime").datetime(2023, 2, 13, 0, 0, 40))
    path = f"{instrumentation.fs_storage}/{sim}/measurements/conversation.jsonl"
    lines = [__import__("json").loads(l) for l in open(path)]
    assert len(lines) == 1
    assert lines[0]["transcript"] == convo
    assert sorted(lines[0]["participants"]) == ["Isabella Rodriguez", "Maria Lopez"]
    import shutil
    shutil.rmtree(f"{instrumentation.fs_storage}/{sim}", ignore_errors=True)


def test_capture_conversations_ignores_none_chat():
    sim = "test_capture_convo_none"
    log = instrumentation.MeasurementLog(sim)
    movements = {"persona": {
        "Isabella Rodriguez": {"movement": [1, 2], "chat": None},
        "Maria Lopez": {"movement": [3, 4], "chat": None},
    }, "meta": {}}
    instrumentation.capture_conversations(
        movements, log, step=1, curr_time=__import__("datetime").datetime(2023, 2, 13, 0, 0, 10))
    import os
    assert not os.path.exists(f"{instrumentation.fs_storage}/{sim}/measurements/conversation.jsonl")
    import shutil
    shutil.rmtree(f"{instrumentation.fs_storage}/{sim}", ignore_errors=True)


def test_probe_relationships_logs_each_ordered_pair(monkeypatch):
    sim = "test_probe_unit"
    log = instrumentation.MeasurementLog(sim)

    def fake_new_retrieve(persona, focal_points, n_count=30):
        return {focal_points[0]: []}

    calls = []
    def fake_summarize(a, b, retrieved):
        calls.append((a.scratch.name, b.scratch.name))
        return f"{a.scratch.name} thinks {b.scratch.name} is a rival"

    monkeypatch.setattr(instrumentation, "new_retrieve", fake_new_retrieve)
    monkeypatch.setattr(instrumentation.converse, "generate_summarize_agent_relationship", fake_summarize)

    isabella = _fake_persona("Isabella Rodriguez", "Isabella", [])
    maria = _fake_persona("Maria Lopez", "Maria", [])
    personas = {"Isabella Rodriguez": isabella, "Maria Lopez": maria}
    instrumentation.probe_relationships(
        personas, log, step=6, curr_time=__import__("datetime").datetime(2023, 2, 13, 0, 1, 0))

    assert set(calls) == {("Isabella Rodriguez", "Maria Lopez"), ("Maria Lopez", "Isabella Rodriguez")}
    path = f"{instrumentation.fs_storage}/{sim}/measurements/relationship_summary.jsonl"
    lines = [__import__("json").loads(l) for l in open(path)]
    assert len(lines) == 2
    assert all(l["source"] == "probe" for l in lines)
    assert {(l["from"], l["to"]) for l in lines} == set(calls)
    import shutil
    shutil.rmtree(f"{instrumentation.fs_storage}/{sim}", ignore_errors=True)


def test_run_headless_instrumented_writes_measurements(monkeypatch):
    import shutil
    import reverie
    import headless
    import instrumentation as instr

    sim = "test_instrumented_run"
    folder = f"{instr.fs_storage}/{sim}"
    shutil.rmtree(folder, ignore_errors=True)

    monkeypatch.setattr(instr, "new_retrieve", lambda persona, fp, n_count=30: {fp[0]: []})
    monkeypatch.setattr(instr.converse, "generate_summarize_agent_relationship",
                        lambda a, b, retrieved: f"{a.scratch.name}->{b.scratch.name}")

    orig_init = reverie.ReverieServer.__init__
    def patched_init(self, fork, sim_code):
        orig_init(self, fork, sim_code)
        for p in self.personas.values():
            monkeypatch.setattr(p, "move", lambda maze, personas, tile, t: ((1, 2), "S", "idle @ home"))
    monkeypatch.setattr(reverie.ReverieServer, "__init__", patched_init)
    monkeypatch.setattr(reverie.ReverieServer, "save", lambda self: None)

    headless.run_headless_instrumented("base_the_ville_isabella_maria", sim, 2, probe_every=1)

    import json as _json
    rel = [_json.loads(l) for l in open(f"{folder}/measurements/relationship_summary.jsonl")]
    assert len(rel) == 4  # 2 ordered pairs x 2 steps
    assert all(r["source"] == "probe" for r in rel)
    assert {(r["from"], r["to"]) for r in rel} == {
        ("Isabella Rodriguez", "Maria Lopez"), ("Maria Lopez", "Isabella Rodriguez")}
    shutil.rmtree(folder, ignore_errors=True)
