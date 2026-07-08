MIN_DROPOUT_RUN = 3


def _low_engagement(card):
    if card.get("is_filler"):
        return True
    return card["end_hook"]["strength"] == 0 and not card["shuang_points"]


def _runs_ge(cards, flags, min_run):
    out, i, n = [], 0, len(flags)
    while i < n:
        if flags[i]:
            j = i
            while j < n and flags[j]:
                j += 1
            if j - i >= min_run:
                out.extend(cards[k]["chapter"] for k in range(i, j))
            i = j
        else:
            i += 1
    return out


def aggregate(cards):
    cards = sorted(cards, key=lambda c: c["chapter"])
    n = len(cards)
    hook_curve = [[c["chapter"], c["end_hook"]["strength"]] for c in cards]
    shuang_density = [[c["chapter"], sum(sp["intensity"] for sp in c["shuang_points"])]
                      for c in cards]
    emotion_curve = [[c["chapter"], c["emotion_tone"]] for c in cards]
    filler_rate = (sum(1 for c in cards if c.get("is_filler")) / n) if n else 0.0
    low = [_low_engagement(c) for c in cards]
    dropout = _runs_ge(cards, low, MIN_DROPOUT_RUN)
    return {
        "hook_curve": hook_curve,
        "shuang_density": shuang_density,
        "emotion_curve": emotion_curve,
        "filler_rate": filler_rate,
        "dropout_risk_chapters": dropout,
    }
