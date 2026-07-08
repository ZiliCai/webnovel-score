import pathlib
from scripts.detect_chapters import detect_chapters

FIX = pathlib.Path(__file__).resolve().parent / "fixtures" / "chapters_sample.txt"

def test_detects_three_chapters():
    ch = detect_chapters(FIX.read_text(encoding="utf-8"))
    assert len(ch) == 3
    assert ch[0]["title"].startswith("第一章")
    assert ch[0]["start_line"] == 1

def test_handles_large_chinese_numeral():
    ch = detect_chapters(FIX.read_text(encoding="utf-8"))
    assert "第一千零一章" in ch[2]["title"]

def test_word_count_positive():
    ch = detect_chapters(FIX.read_text(encoding="utf-8"))
    assert all(c["word_count"] > 0 for c in ch)

def test_no_chapters_returns_empty():
    assert detect_chapters("这是一段没有章节标题的纯文本。") == []
