REQUIRED_KEYS = ("Requested Mode","Effective Mode","Fallback",
                 "Rubric","Rubric Source","评分范围")


def validate_report(md_text):
    return [k for k in REQUIRED_KEYS if f"{k}:" not in md_text]
