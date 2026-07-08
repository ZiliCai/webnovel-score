import re, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

def _frontmatter(md_text):
    m = re.match(r"^---\n(.*?)\n---\n", md_text, re.S)
    return m.group(1) if m else ""

def test_skill_has_name_and_description():
    fm = _frontmatter((ROOT / "SKILL.md").read_text(encoding="utf-8"))
    assert "name: webnovel-score" in fm
    assert "description:" in fm
    assert "网文评分" in fm and "商业评分" in fm
