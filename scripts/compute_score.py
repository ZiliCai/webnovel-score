import math

_GRADE_BANDS = [(85, "S"), (75, "A"), (60, "B"), (0, "C")]


def _grade(total):
    for threshold, g in _GRADE_BANDS:
        if total >= threshold:
            return g
    return "C"


def compute_overall(dimension_scores, weights):
    missing = [d for d in weights if d not in dimension_scores]
    if missing:
        raise ValueError(f"dimension_scores 缺少维度: {missing}")
    # weights 和为 100；四舍五入（round-half-up），非银行家圆整
    raw = sum(dimension_scores[d] * weights[d] for d in weights) / 100
    total = math.floor(raw + 0.5)
    return {"weighted_total": total, "grade": _grade(total)}
