from scripts.scan_moral_drift import scan_moral_findings, scan_dimension_rationales


def assert_calibration(baokuan, pujie, margin=10):
    return (baokuan["weighted_total"] - pujie["weighted_total"]) >= margin


def stance_clean(synthesis):
    dirty_issues = scan_moral_findings(synthesis.get("hard_issues", []))
    dirty_dims = scan_dimension_rationales(synthesis.get("dimensions", []))
    return dirty_issues == [] and dirty_dims == []
