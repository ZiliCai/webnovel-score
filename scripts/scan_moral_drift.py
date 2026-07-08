"""检出道德漂移 finding：含道德评判词且未归因到合法商业机制的，判为应删除。"""

MORAL_TOKENS = ["男凝", "物化", "刻板印象", "价值观", "进步", "尊重",
                "爹味", "低级", "歧视", "不正确"]

# 唯一合法的商业风险机制（对应立场声明 §3 ①②及其派生表述）
ALLOWED_MECHANISMS = {
    "平台审核风险", "劝退目标读者盘", "劝退目标读者",
    "开局劝退", "中段掉读", "节奏拖沓", "钩子缺失",
}


def _finding_text(f):
    return " ".join(str(f.get(k, "")) for k in ("issue", "rationale", "fix"))


def scan_moral_findings(findings):
    flagged = []
    for f in findings:
        has_moral = any(tok in _finding_text(f) for tok in MORAL_TOKENS)
        grounded = f.get("commercial_mechanism", "") in ALLOWED_MECHANISMS
        if has_moral and not grounded:
            flagged.append(f)
    return flagged
