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
