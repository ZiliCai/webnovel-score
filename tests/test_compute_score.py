import pytest
from scripts.compute_score import compute_overall
from scripts.load_rubric import load_weights, DIMENSIONS


def test_all_100_gives_100_S():
    scores = {d: 100 for d in DIMENSIONS}
    out = compute_overall(scores, load_weights("fanqie"))
    assert out["weighted_total"] == 100
    assert out["grade"] == "S"


def test_weighted_average_and_grade():
    scores = {"开局抓力":90,"爽点系统":80,"追读钩子":70,
              "节奏与留存":70,"题材卖点":60,"长线承载":50}
    # fanqie: (90*30+80*20+70*15+70*15+60*12+50*8)/100
    #        = (2700+1600+1050+1050+720+400)/100 = 7520/100 = 75.2 -> 75
    out = compute_overall(scores, load_weights("fanqie"))
    assert out["weighted_total"] == 75
    assert out["grade"] == "A"   # 75-84


def test_grade_boundaries():
    def grade_of(v):
        s = {d: v for d in DIMENSIONS}
        return compute_overall(s, load_weights("fanqie"))["grade"]
    assert grade_of(85) == "S"
    assert grade_of(84) == "A"
    assert grade_of(75) == "A"
    assert grade_of(74) == "B"
    assert grade_of(60) == "B"
    assert grade_of(59) == "C"


def test_round_half_up_at_boundary():
    # fanqie: 95*30 + 80*(20+15+15+12+8) = 2850 + 5600 = 8450 -> 84.5 -> half-up 85 -> S
    scores = {"开局抓力":95,"爽点系统":80,"追读钩子":80,
              "节奏与留存":80,"题材卖点":80,"长线承载":80}
    out = compute_overall(scores, load_weights("fanqie"))
    assert out["weighted_total"] == 85
    assert out["grade"] == "S"


def test_missing_dimension_raises():
    scores = {"开局抓力":80}  # missing 5
    with pytest.raises(ValueError):
        compute_overall(scores, load_weights("fanqie"))
