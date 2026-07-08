import json, pathlib
from scripts.aggregate_curves import aggregate

FIX = pathlib.Path(__file__).resolve().parent / "fixtures" / "signal_cards_sample.json"
CARDS = json.loads(FIX.read_text(encoding="utf-8"))

def test_filler_rate():
    out = aggregate(CARDS)
    assert abs(out["filler_rate"] - 3/6) < 1e-9

def test_dropout_run_detected():
    out = aggregate(CARDS)
    assert out["dropout_risk_chapters"] == [3, 4, 5]

def test_short_run_not_flagged():
    # 只有 1 章低投入，不足 3，不标
    cards = [dict(CARDS[0]), dict(CARDS[2]), dict(CARDS[0])]
    for i, c in enumerate(cards): c["chapter"] = i + 1
    assert aggregate(cards)["dropout_risk_chapters"] == []

def test_curves_length_matches():
    out = aggregate(CARDS)
    assert len(out["hook_curve"]) == 6
    assert out["hook_curve"][0] == [1, 3]

def test_empty_input():
    out = aggregate([])
    assert out["filler_rate"] == 0.0
    assert out["dropout_risk_chapters"] == []
