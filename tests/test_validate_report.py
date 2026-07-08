import pathlib
from scripts.validate_report import validate_report, REQUIRED_KEYS

REF = pathlib.Path(__file__).resolve().parents[1] / "references"


def test_template_itself_passes():
    assert validate_report((REF / "报告模板.md").read_text(encoding="utf-8")) == []


def test_missing_key_detected():
    partial = "Requested Mode: full\nRubric: fanqie\n"
    missing = validate_report(partial)
    assert "Effective Mode" in missing
    assert "Rubric Source" in missing


def test_required_keys_frozen():
    assert REQUIRED_KEYS == ("Requested Mode","Effective Mode","Fallback",
                             "Rubric","Rubric Source","评分范围")
