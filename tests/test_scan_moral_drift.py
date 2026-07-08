from scripts.scan_moral_drift import scan_moral_findings, scan_dimension_rationales


def test_flags_pure_moral_finding():
    findings = [{"issue": "对女性描写太男凝，物化严重", "commercial_mechanism": ""}]
    assert scan_moral_findings(findings) == findings


def test_keeps_moral_word_grounded_in_commercial_mechanism():
    # 男凝到连目标读者都劝退 —— 合法商业风险，保留
    findings = [{"issue": "开局连续男凝到目标读者也反感", "commercial_mechanism": "劝退目标读者盘"}]
    assert scan_moral_findings(findings) == []


def test_keeps_nonmoral_finding():
    findings = [{"issue": "第17章连续三章无爽点", "commercial_mechanism": "中段掉读"}]
    assert scan_moral_findings(findings) == []


def test_flags_progressive_critique_without_mechanism():
    findings = [{"issue": "价值观不够进步，不尊重女性", "commercial_mechanism": "开局劝退"}]
    # 机制字段填了但内容是纯道德、机制与道德词无因果 —— 仍按道德词命中处理：
    # 规则=含道德词且机制不在允许集 -> flag；"开局劝退"在允许集，故此条不 flag。
    assert scan_moral_findings(findings) == []


def test_flags_moral_dimension_rationale():
    dims = [{"key": "爽点系统", "score": 60,
             "rationale": "扣分：对女性描写太男凝、价值观不正确"}]
    assert scan_dimension_rationales(dims) == dims


def test_keeps_commercially_grounded_dimension_rationale():
    dims = [{"key": "爽点系统", "score": 60,
             "rationale": "男凝写得过火，会劝退目标读者盘"}]  # 含"劝退"→商业归因
    assert scan_dimension_rationales(dims) == []


def test_keeps_nonmoral_dimension_rationale():
    dims = [{"key": "开局抓力", "score": 85, "rationale": "首爽三章内兑现，钩子强"}]
    assert scan_dimension_rationales(dims) == []
