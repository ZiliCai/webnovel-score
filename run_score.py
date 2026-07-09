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
OPENING_CHAPTERS = 6    # 开局深读章数（设计为 6，必要时 harness 可加大到 10）
BATCH_CHARS = 50000     # Stage 2 每批字数预算（约 25-30k tokens，装得下、留余量）


def _stance():
    return (REF / "立场声明.md").read_text(encoding="utf-8")


def _prompt(name):
    """读 prompt 文件并注入立场声明（每个评分 prompt 都必须做）。"""
    text = (REF / name).read_text(encoding="utf-8")
    if "{{立场声明}}" not in text:
        raise ValueError(f"{name} 缺少 {{{{立场声明}}}} 注入点")
    return text.replace("{{立场声明}}", _stance())


def _parse_json(raw):
    """从模型输出抽出 JSON——容忍前置散文分析 + ```json 代码块 + 裸 JSON。"""
    candidates = []
    blocks = re.findall(r"```(?:json)?\s*(.+?)\s*```", raw, re.S)
    candidates.extend(reversed(blocks))       # 代码块，取最后一个（通常是最终结果）
    # 无围栏时：谁的开括号更靠前谁是外层（对象 { 或 数组 [）
    fo, fa = raw.find("{"), raw.find("[")
    if fa != -1 and (fo == -1 or fa < fo):
        candidates.append(raw[fa:raw.rfind("]") + 1])   # 外层是数组
    elif fo != -1:
        candidates.append(raw[fo:raw.rfind("}") + 1])   # 外层是对象
    candidates.append(raw.strip())            # 整段兜底
    last = None
    for c in candidates:
        try:
            return json.loads(c)
        except Exception as e:
            last = e
    raise ValueError(f"无法从输出中解析 JSON：{last}")


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


def _ask_batch(llm_call, prompt, payload, expect_len, validate_card=None, retries=2):
    """发一批章节，要 {"batch_summary": str, "cards": [...]}，校验卡数与每张卡。"""
    msg = f"{prompt}\n\n{payload}"
    last = None
    for _ in range(retries + 1):
        raw = llm_call(msg)
        try:
            obj = _parse_json(raw)
        except Exception as e:
            last = f"输出不是合法 JSON（{e}），只返回含 batch_summary 与 cards 的 JSON 对象。"
            msg = f"{prompt}\n\n{payload}\n\n{last}"
            continue
        if isinstance(obj, list):                     # 模型偷懒只回数组 → 容错包一层
            obj = {"batch_summary": "", "cards": obj}
        cards = obj.get("cards")
        if not isinstance(cards, list) or len(cards) != expect_len:
            got = len(cards) if isinstance(cards, list) else type(cards).__name__
            last = f"cards 应为 {expect_len} 张（每章一张、按章序），拿到 {got}。"
            msg = f"{prompt}\n\n{payload}\n\n{last}"
            continue
        if validate_card:
            bad = [(k, validate_card(o)[:2]) for k, o in enumerate(cards) if validate_card(o)]
            if bad:
                last = f"部分卡不合 schema：{bad[:3]}，修正后重出完整对象。"
                msg = f"{prompt}\n\n{payload}\n\n{last}"
                continue
        return obj
    raise RuntimeError(f"逐章信号批次未能产出合规输出：{last}")


def _chapter_text(lines, chapters, i):
    start = chapters[i]["start_line"] - 1
    end = chapters[i + 1]["start_line"] - 1 if i + 1 < len(chapters) else len(lines)
    return "\n".join(lines[start:end])


def _batches(chapters, budget):
    """把章节下标按字数预算分批：单章超预算则自成一批。返回 [[idx,...], ...]。"""
    out, cur, cur_len = [], [], 0
    for i, c in enumerate(chapters):
        wc = c.get("word_count") or 0
        if cur and cur_len + wc > budget:
            out.append(cur)
            cur, cur_len = [], 0
        cur.append(i)
        cur_len += wc
    if cur:
        out.append(cur)
    return out


def score_book(text, llm_call, platform="fanqie", book_name="未命名",
               opening_chapters=OPENING_CHAPTERS, spot_check=True, counter_check=True):
    """跑完整 Stage 0-4.5，返回带 weighted_total/grade 的 synthesis dict。

    spot_check=True：Stage 3.5 抽 2-3 个中后段章节全文核验（优先掉读风险章）。
    counter_check=True：Stage 4.5 反调 agent 有据下调 + 道德 scrub（失败不阻断）。
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

    # Stage 2：逐章信号 map — 按字数预算分批，每批一个子 agent 出一组信号卡 + 批次剧情摘要
    # （90 章 ≈ 几批，不是 90 次调用；同批多章由同一调用判、同一把尺子）
    cards, batch_summaries = [], []
    for batch in _batches(chapters, BATCH_CHARS):
        parts = []
        for i in batch:
            c = chapters[i]
            parts.append(f"=== 第{c['number']}章 {c['title']}（约{c['word_count']}字）===\n"
                         f"{_chapter_text(lines, chapters, i)}")
        payload = "以下是连续若干章，对每一章各产一张信号卡：\n\n" + "\n\n".join(parts)
        env = _ask_batch(llm_call, _prompt("prompt-逐章信号.md"), payload,
                         expect_len=len(batch), validate_card=validate_signal_card)
        for idx, card in zip(batch, env["cards"]):
            card.setdefault("chapter", chapters[idx]["number"])
            cards.append(card)
        if env.get("batch_summary"):
            batch_summaries.append({
                "chapters": f"{chapters[batch[0]]['number']}-{chapters[batch[-1]]['number']}",
                "summary": env["batch_summary"]})

    # Stage 3：曲线聚合（纯脚本）
    curves = aggregate(cards)

    # Stage 3.5：中后段抽查深读（核验信号卡 + 爽点执行质量；优先掉读风险章）
    spot = None
    if spot_check:
        pool = list(range(n_open, len(chapters)))
        if len(pool) > 2:
            risky_set = set(curves["dropout_risk_chapters"])
            picks = [i for i in pool if chapters[i]["number"] in risky_set][:2]
            for pos in (0.5, 0.85):
                cand = pool[min(int(len(pool) * pos), len(pool) - 1)]
                if cand not in picks:
                    picks.append(cand)
            by_ch = {c["chapter"]: c for c in cards}
            parts = []
            for i in sorted(picks[:3]):
                ch = chapters[i]
                parts.append(
                    f"=== 第{ch['number']}章 {ch['title']} ===\n"
                    f"[先前信号卡] {json.dumps(by_ch.get(ch['number'], {}), ensure_ascii=False)}\n"
                    f"[原文]\n{_chapter_text(lines, chapters, i)}")
            spot = _ask_json(llm_call, _prompt("prompt-抽查深读.md"),
                             "抽查章节（含各章先前的信号卡）：\n\n" + "\n\n".join(parts))

    # Stage 4：维度评分（LLM 判 6 维）+ 脚本算总分
    compressed = json.dumps({"opening_card": opening_card, "curves": curves,
                             "batch_summaries": batch_summaries, "spot_check": spot},
                            ensure_ascii=False)
    synth = _ask_json(
        llm_call, _prompt("prompt-维度评分.md"),
        f"开局评分卡 + 聚合曲线（只读这些，不读原文全书）：\n{compressed}",
        validate=validate_synthesis)
    dim_scores = {d["key"]: d["score"] for d in synth["dimensions"]}
    overall = compute_overall(dim_scores, load_weights(platform))
    synth["weighted_total"] = overall["weighted_total"]
    synth["grade"] = overall["grade"]

    # Stage 4.5a：反调 cross-check（LLM，对照曲线/抽查证据下调 + 道德 scrub；失败不阻断）
    if counter_check:
        try:
            counter = _ask_json(
                llm_call, _prompt("prompt-反调.md"),
                "待反调的评分 + 证据：\n" + json.dumps(
                    {"scoring": {k: v for k, v in synth.items() if not k.startswith("_")},
                     "curves": curves, "spot_check": spot,
                     "batch_summaries": batch_summaries}, ensure_ascii=False))
            for a in counter.get("score_adjustments") or []:
                k, to = a.get("key"), a.get("to")
                if k in dim_scores and isinstance(to, int) and 0 <= to <= 100:
                    dim_scores[k] = to
                    for d in synth["dimensions"]:
                        if d["key"] == k:
                            d["score"] = to
                            d["rationale"] += f"（反调调整：{a.get('reason', '')}）"
            removed = counter.get("removed_moral_findings") or []
            if removed:
                synth["hard_issues"] = [
                    h for h in synth["hard_issues"]
                    if not any(r and (r in h.get("issue", "") or h.get("issue", "") in r)
                               for r in removed)]
            overall = compute_overall(dim_scores, load_weights(platform))
            synth["weighted_total"] = overall["weighted_total"]
            synth["grade"] = overall["grade"]
            synth["_counter_check"] = counter
        except Exception as e:
            synth["_counter_check_error"] = str(e)   # 反调挂了保留原分，不阻断

    # Stage 4.5b：机械道德兜底（脚本层，跨模型必跑）
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
