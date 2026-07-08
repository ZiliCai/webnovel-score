from scripts.scan_moral_drift import scan_moral_findings


def assert_calibration(baokuan, pujie, margin=10):
    return (baokuan["weighted_total"] - pujie["weighted_total"]) >= margin


def stance_clean(synthesis):
    return scan_moral_findings(synthesis.get("hard_issues", [])) == []
