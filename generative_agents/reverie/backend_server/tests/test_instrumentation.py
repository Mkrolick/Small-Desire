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
