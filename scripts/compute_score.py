_GRADE_BANDS = [(85, "S"), (75, "A"), (60, "B"), (0, "C")]


def _grade(total):
    for threshold, g in _GRADE_BANDS:
        if total >= threshold:
            return g
    return "C"


def compute_overall(dimension_scores, weights):
    # weights 和为 100，加权平均 = Σ(score*weight)/100
    total = round(sum(dimension_scores[d] * weights[d] for d in weights) / 100)
    return {"weighted_total": total, "grade": _grade(total)}
