import pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8")

REFERENCED = [
    "references/立场声明.md","references/rubric.md","references/weights.json",
    "references/prompt-开局深读.md","references/prompt-逐章信号.md",
    "references/prompt-维度评分.md","references/prompt-反调.md","references/报告模板.md",
    "schemas/signal_card.schema.json","schemas/synthesis.schema.json",
    "scripts/detect_chapters.py","scripts/aggregate_curves.py",
    "scripts/compute_score.py","scripts/scan_moral_drift.py",
    "scripts/validate_output.py","scripts/load_rubric.py","scripts/validate_report.py",
]

def test_all_referenced_files_exist_and_cited():
    for rel in REFERENCED:
        assert (ROOT / rel).exists(), f"缺文件 {rel}"
        assert rel in SKILL, f"SKILL.md 未引用 {rel}"

def test_covers_all_stages():
    for s in ["Stage 0","Stage 1","Stage 2","Stage 3","Stage 4","Stage 5"]:
        assert s in SKILL

def test_has_degrade_and_sampling_rules():
    assert "sequential" in SKILL          # 无子代理降级
    assert "采样" in SKILL and "log" in SKILL  # 大书采样须 log
    assert "embedded fallback" in SKILL   # rubric 不可读回退
    assert "拆文库" in SKILL               # 自适应快路
