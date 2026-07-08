import pathlib
REF = pathlib.Path(__file__).resolve().parents[1] / "references"

PROMPTS = ["prompt-开局深读.md","prompt-逐章信号.md","prompt-维度评分.md","prompt-反调.md"]

def test_every_prompt_injects_stance():
    for p in PROMPTS:
        t = (REF / p).read_text(encoding="utf-8")
        assert "{{立场声明}}" in t, f"{p} 未注入立场声明"

def test_signal_prompt_declares_schema_fields():
    t = (REF / "prompt-逐章信号.md").read_text(encoding="utf-8")
    for f in ["end_hook","shuang_points","emotion_tone","is_filler","commercial_flags"]:
        assert f in t

def test_synthesis_prompt_declares_fields():
    t = (REF / "prompt-维度评分.md").read_text(encoding="utf-8")
    for f in ["dimensions","weighted_total","grade","hard_issues","commercial_mechanism"]:
        assert f in t

def test_synthesis_prompt_guards_execution_over_density():
    t = (REF / "prompt-维度评分.md").read_text(encoding="utf-8")
    assert "执行质量" in t
    assert "不得因数量多而给高分" in t

def test_counter_prompt_mentions_moral_scrub():
    t = (REF / "prompt-反调.md").read_text(encoding="utf-8")
    assert "道德" in t and "removed_moral_findings" in t
