"""检出道德漂移 finding：含道德评判词且未归因到合法商业机制的，判为应删除。"""

MORAL_TOKENS = ["男凝", "物化", "刻板印象", "价值观", "进步", "尊重",
                "爹味", "低级", "歧视", "不正确"]

# 唯一合法的商业风险机制（对应立场声明 §3 ①②及其派生表述）
ALLOWED_MECHANISMS = {
    "平台审核风险", "劝退目标读者盘", "劝退目标读者",
    "开局劝退", "中段掉读", "节奏拖沓", "钩子缺失",
}


# 自由文本层的商业归因关键词（维度 rationale 没有 commercial_mechanism 字段，只能从文本判断）
_GROUNDING_KEYWORDS = ("审核", "封禁", "下架", "劝退", "掉读", "钩子", "节奏")


def _has_moral(text):
    return any(tok in text for tok in MORAL_TOKENS)


def _finding_text(f):
    return " ".join(str(f.get(k, "")) for k in ("issue", "rationale", "fix"))


def scan_moral_findings(findings):
    flagged = []
    for f in findings:
        has_moral = _has_moral(_finding_text(f))
        grounded = f.get("commercial_mechanism", "") in ALLOWED_MECHANISMS
        if has_moral and not grounded:
            flagged.append(f)
    return flagged


def scan_dimension_rationales(dimensions):
    """维度 rationale 里出现道德评判词、又没有任何商业归因关键词的，判为道德漂移。"""
    flagged = []
    for d in dimensions:
        rationale = str(d.get("rationale", ""))
        if _has_moral(rationale) and not any(k in rationale for k in _GROUNDING_KEYWORDS):
            flagged.append(d)
    return flagged
