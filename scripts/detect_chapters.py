import re

# 覆盖阿拉伯数字与中文数字（含 百/千/两/零），匹配行首「第…章」
_CHAP_RE = re.compile(r"^\s*第[0-9零一二三四五六七八九十百千两]+章[^\n]*")


def detect_chapters(text):
    lines = text.splitlines()
    heads = []  # (line_index0, title)
    for i, line in enumerate(lines):
        if _CHAP_RE.match(line):
            heads.append((i, line.strip()))
    result = []
    for idx, (li, title) in enumerate(heads):
        end = heads[idx + 1][0] if idx + 1 < len(heads) else len(lines)
        body = "\n".join(lines[li + 1:end])
        wc = len(re.sub(r"\s", "", body))
        result.append({
            "number": idx + 1,
            "title": title,
            "start_line": li + 1,     # 1-based，供落盘边界表
            "word_count": wc,
        })
    return result
