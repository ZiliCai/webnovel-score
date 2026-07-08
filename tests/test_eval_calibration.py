import json, pathlib
from scripts.eval_calibration import assert_calibration, stance_clean

FX = pathlib.Path(__file__).resolve().parent / "fixtures"
def load(n): return json.loads((FX / n).read_text(encoding="utf-8"))

def test_baokuan_beats_pujie():
    assert assert_calibration(load("synthesis_baokuan.json"),
                              load("synthesis_pujie.json"), margin=10) is True

def test_calibration_fails_when_close():
    a = {"weighted_total": 70}; b = {"weighted_total": 68}
    assert assert_calibration(a, b, margin=10) is False

def test_stance_dirty_findings_flagged():
    dirty = {"hard_issues": load("findings_moral_drift.json")}
    assert stance_clean(dirty) is False

def test_stance_clean_when_only_commercial():
    clean = {"hard_issues": [{"issue":"掉读","commercial_mechanism":"中段掉读"}]}
    assert stance_clean(clean) is True
