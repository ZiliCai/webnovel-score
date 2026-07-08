import pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
TEXT = (ROOT / "references" / "立场声明.md")

EXEMPTIONS = ["男凝","雌竞","慕强","扮猪吃虎","后宫","种马","复仇虐渣","道德灰色主角","金手指"]
MORAL_BAN_WORDS = ["物化","刻板印象","价值观","进步","尊重","爹味","低级"]

def test_stance_has_all_required_parts():
    t = TEXT.read_text(encoding="utf-8")
    # 四条 clause 编号
    for n in ["1.","2.","3.","4."]:
        assert n in t
    # 豁免清单齐全
    for w in EXEMPTIONS:
        assert w in t, f"缺豁免项 {w}"
    # 唯一风险口径的两条商业机制
    assert "平台" in t and "审核" in t
    assert "劝退" in t and "目标读者" in t
    # 反道德漂移自检点名的禁词
    for w in MORAL_BAN_WORDS:
        assert w in t, f"自检禁词缺 {w}"
    # 材料合法性块
    assert "材料合法性" in t
