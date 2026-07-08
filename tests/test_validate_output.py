from scripts.validate_output import validate_signal_card, validate_synthesis

VALID_CARD = {
    "chapter": 42, "title": "第42章 测试", "word_count": 3120,
    "end_hook": {"strength": 2, "type": "悬念未解", "quote": "他回头，门开了。"},
    "shuang_points": [{"type": "打脸", "intensity": 3, "quote": "一巴掌。"}],
    "emotion_tone": "爽", "conflict_closed": True, "info_gain": True,
    "is_filler": False, "commercial_flags": [],
}

VALID_SYNTH = {
    "dimensions": [{"key": "开局抓力", "score": 82, "anchor_band": "75-89",
                    "evidence": ["第3章: 引用"], "rationale": "…"}],
    "weighted_total": 78, "grade": "A", "signing_verdict": "可签。",
    "hard_issues": [{"issue": "x", "chapter": 17, "quote": "q",
                     "commercial_mechanism": "中段掉读", "fix": "f"}],
    "dropout_risk_chapters": [17],
}

def test_valid_card_passes():
    assert validate_signal_card(VALID_CARD) == []

def test_card_bad_enum_fails():
    bad = dict(VALID_CARD, emotion_tone="忧郁")  # 不在枚举
    assert validate_signal_card(bad)

def test_card_missing_hook_fails():
    bad = {k: v for k, v in VALID_CARD.items() if k != "end_hook"}
    assert validate_signal_card(bad)

def test_valid_synth_passes():
    assert validate_synthesis(VALID_SYNTH) == []

def test_hard_issue_without_mechanism_fails():
    bad = {**VALID_SYNTH,
           "hard_issues": [{"issue": "x", "chapter": 1, "quote": "q", "fix": "f"}]}
    assert validate_synthesis(bad)  # 缺 commercial_mechanism
