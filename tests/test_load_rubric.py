from scripts.load_rubric import load_weights, DIMENSIONS


def test_six_dimensions():
    assert DIMENSIONS == ("开局抓力", "爽点系统", "追读钩子", "节奏与留存", "题材卖点", "长线承载")


def test_each_platform_sums_to_100():
    for p in ("fanqie", "qidian", "zhihu", "generic"):
        w = load_weights(p)
        assert set(w) == set(DIMENSIONS)
        assert sum(w.values()) == 100, f"{p} 权重和≠100"


def test_qidian_favors_longline():
    assert load_weights("qidian")["长线承载"] > load_weights("fanqie")["长线承载"]
    assert load_weights("qidian")["开局抓力"] < load_weights("fanqie")["开局抓力"]


def test_unknown_platform_falls_back_generic():
    assert load_weights("zhihu_unknown_xyz") == load_weights("generic")
