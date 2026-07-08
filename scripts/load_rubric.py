import json, pathlib

_REF = pathlib.Path(__file__).resolve().parents[1] / "references"
DIMENSIONS = ("开局抓力", "爽点系统", "追读钩子", "节奏与留存", "题材卖点", "长线承载")


def _table():
    return json.loads((_REF / "weights.json").read_text(encoding="utf-8"))


def load_weights(platform):
    t = _table()
    return t.get(platform, t["generic"])
