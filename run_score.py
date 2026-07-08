"""webnovel-score 参考编排器（平台 / 模型无关）。

用法：插入你自己的 `llm_call(prompt: str) -> str`（返回模型原始文本；对评分
prompt 必须返回单个 JSON 对象），即可在任意 harness 上跑——Claude Code /
OpenCode / Hermes / 纯 Python 都行。scripts/* 是纯 Python、永不调用 LLM；
唯一调用模型的地方就是你传进来的 `llm_call`。

    from run_score import score_book
    def llm_call(prompt):            # 你的 harness / Kimi / 任意模型
        return my_model.generate(prompt)
    result = score_book(open("book.txt", encoding="utf-8").read(), llm_call,
                        platform="fanqie", book_name="某本书")
    print(result["weighted_total"], result["grade"])
    print(result["_moral_drift_flagged"])   # 应为 []；非空表示模型出现道德漂移
"""
import json
import re
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))  # 让 `from scripts...` 无视 cwd 都能 import

from scripts.detect_chapters import detect_chapters
from scripts.aggregate_curves import aggregate
from scripts.compute_score import compute_overall
from scripts.load_rubric import load_weights
from scripts.validate_output import validate_signal_card, validate_synthesis
from scripts.scan_moral_drift import scan_moral_findings, scan_dimension_rationales

REF = ROOT / "references"
OPENING_CHAPTERS = 6  # 开局深读章数（设计为 6，必要时 harness 可加大到 10）


def _stance():
    return (REF / "立场声明.md").read_text(encoding="utf-8")


def _prompt(name):
    """读 prompt 文件并注入立场声明（每个评分 prompt 都必须做）。"""
    text = (REF / name).read_text(encoding="utf-8")
    if "{{立场声明}}" not in text:
        raise ValueError(f"{name} 缺少 {{{{立场声明}}}} 注入点")
    return text.replace("{{立场声明}}", _stance())


def _parse_json(raw):
    """容忍模型偶尔加的 ```json 围栏。"""
    s = raw.strip()
    s = re.sub(r"^```(?:json)?\s*", "", s)
    s = re.sub(r"\s*```$", "", s)
    return json.loads(s)


def _ask_json(llm_call, prompt, payload, validate=None, retries=2):
    """发 prompt+payload，解析 JSON，可选 schema 校验，不合规就带原因重试。"""
    msg = f"{prompt}\n\n{payload}"
    last = None
    for _ in range(retries + 1):
        raw = llm_call(msg)
        try:
            obj = _parse_json(raw)
        except Exception as e:
            last = f"上次输出不是合法 JSON（{e}），请只返回一个 JSON 对象、不要围栏。"
            msg = f"{prompt}\n\n{payload}\n\n{last}"
            continue
        if validate:
            errs = validate(obj)
            if errs:
                last = f"上次 JSON 不符合 schema：{errs[:3]}，修正后只返回 JSON。"
                msg = f"{prompt}\n\n{payload}\n\n{last}"
                continue
        return obj
    raise RuntimeError(f"LLM 未能产出合规 JSON：{last}")


def _chapter_text(lines, chapters, i):
    start = chapters[i]["start_line"] - 1
    end = chapters[i + 1]["start_line"] - 1 if i + 1 < len(chapters) else len(lines)
    return "\n".join(lines[start:end])


def score_book(text, llm_call, platform="fanqie", book_name="未命名",
               opening_chapters=OPENING_CHAPTERS):
    """跑完整 Stage 0-4.5，返回带 weighted_total/grade 的 synthesis dict。

    额外键 `_moral_drift_flagged`：机械兜底扫出的道德漂移条目（hard_issues +
    dimensions[].rationale）。应为 []；非空说明模型没守住商业中立，需处理。
    """
    chapters = detect_chapters(text)
    if not chapters:
        raise ValueError("识别不到章节——检查原文的章节标题格式（第N章…）。")
    lines = text.splitlines()

    # Stage 1：开局深读（前 N 章全文）
    n_open = min(opening_chapters, len(chapters))
    opening = "\n\n".join(_chapter_text(lines, chapters, i) for i in range(n_open))
    opening_card = _ask_json(
        llm_call, _prompt("prompt-开局深读.md"),
        f"前 {n_open} 章全文：\n{opening}")

    # Stage 2：逐章信号 map（每章一张信号卡；harness 可并行）
    cards = []
    for i in range(len(chapters)):
        c = chapters[i]
        card = _ask_json(
            llm_call, _prompt("prompt-逐章信号.md"),
            f"章节编号：第{c['number']}章\n标题：{c['title']}\n字数约：{c['word_count']}\n\n"
            f"章节原文：\n{_chapter_text(lines, chapters, i)}",
            validate=validate_signal_card)
        card.setdefault("chapter", c["number"])
        cards.append(card)

    # Stage 3：曲线聚合（纯脚本）
    curves = aggregate(cards)

    # Stage 4：维度评分（LLM 判 6 维）+ 脚本算总分
    compressed = json.dumps({"opening_card": opening_card, "curves": curves},
                            ensure_ascii=False)
    synth = _ask_json(
        llm_call, _prompt("prompt-维度评分.md"),
        f"开局评分卡 + 聚合曲线（只读这些，不读原文全书）：\n{compressed}",
        validate=validate_synthesis)
    dim_scores = {d["key"]: d["score"] for d in synth["dimensions"]}
    overall = compute_overall(dim_scores, load_weights(platform))
    synth["weighted_total"] = overall["weighted_total"]
    synth["grade"] = overall["grade"]

    # Stage 4.5：机械道德兜底（脚本层，跨模型必跑）
    synth["_moral_drift_flagged"] = (
        scan_moral_findings(synth.get("hard_issues", []))
        + scan_dimension_rationales(synth.get("dimensions", [])))
    synth["_book_name"] = book_name
    synth["_platform"] = platform
    return synth


if __name__ == "__main__":
    print("这是参考编排器，需要你提供 llm_call。示例：", file=sys.stderr)
    print("  from run_score import score_book", file=sys.stderr)
    print("  score_book(text, my_llm_call, platform='fanqie')", file=sys.stderr)
    print("scripts/* 为纯 Python，不含任何 LLM 调用；模型接入点只有 llm_call。",
          file=sys.stderr)
