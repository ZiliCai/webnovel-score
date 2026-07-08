---
name: webnovel-score
version: 0.2.0
description: "长篇网文商业潜力/签约概率评分。独立、模型无关、商业中立（目标读者+平台责编视角，不做道德评判）。混合深度 map-reduce：开局全读+逐章信号+压缩聚合+holistic judge。触发：/网文评分、/商业评分、「这书能签吗」「打个分」。"
---
# webnovel-score：网文商业评分

判长篇网文的商业潜力/签约概率。独立、模型无关、商业中立。

## 你是编排器（先读这条 · 最重要）
你**不是**「一个人读完整本书然后打分」。你是**编排器**：把评分拆成一批**彼此隔离、上下文互不共享、各自独立**的子任务，用工具去跑——

- **确定性步骤**（切章 / 聚合 / 算分 / 校验 / 道德兜底）：**用 bash 运行**对应 `scripts/*.py`。
- **判断步骤**（开局深读 / 逐章信号 / 维度评分 / 反调）：**为每个单元派一个独立子 agent**（用你的 Task / 子任务工具）。每个子 agent 拿到的上下文**只有它那一份材料** + 注入了 `references/立场声明.md` 的 prompt；它产出结果后即销毁，不留在你的上下文里。
- **铁律**：禁止在你自己的单一上下文里一次读完整本书打分。逐章必须**一章一个独立子 agent**。只有当前环境没有子任务工具、或你已在子代理内时，才降级为顺序处理（Effective Mode: sequential），并在报告里声明。

> 不想手工编排、或所在 harness 是「一轮回答」型（无 Task 工具）：直接用 `run_score.py`——它已把下面 Stage 0-4.5 写成固定代码，插入你的 `llm_call` 即跑，不依赖 harness 的子 agent 能力。

## 立场（最高优先）
每个判断子 agent 的 prompt 运行前，把 `references/立场声明.md` 全文替换进 prompt 里的 `{{立场声明}}` 占位。禁止任何道德/价值观理由扣分或产生 finding——见立场声明第 4 条，并由 `scripts/scan_moral_drift.py` 机械兜底。

## Stage 0 · 定位切章（确定性 · bash）
1. 确认书名 / 原文路径 / 目标平台。
2. **自适应快路**：同目录若有 `拆文库/{书名}/` 章节摘要，直接读来替代 Stage 2 提取（可选、纯读文件）；无则继续。
3. **bash 运行** `scripts/detect_chapters.py` 切章，得章节边界表。识别不到 → 请用户确认格式。

## Stage 1 · 开局深读（一个独立子 agent）
派**一个独立子 agent**：它的上下文只有前 6 章原文（前 6 章内无首爽或核心钩子则延到前 10 章封顶；不足 6 章全读）+ 注入立场声明的 `references/prompt-开局深读.md`。它产出开局评分卡后即销毁。

## Stage 2 · 逐章信号 MAP（每章一个独立子 agent）
这一步是 map：**每一章派一个独立子 agent——单元之间上下文完全隔离、互不共享，每个子 agent 只读它负责的那一章** + 注入立场声明的 `references/prompt-逐章信号.md`，产出该章信号卡。

- **并发**：这些子 agent 彼此独立，**并发派发**（一批 5-8 个）；一批回收后再派下一批。
- **降级**：当前环境没有子任务工具、或你已在子代理内 → 顺序分批处理（Effective Mode: sequential），语义一致、只是慢。
- 每张信号卡按 `schemas/signal_card.schema.json`、**bash 运行** `scripts/validate_output.py` 校验；不合规就让该章子 agent 重出。
- **大书(>200 章)**：钩子 / 爽点用便宜模型全量扫，仅对曲线标出的掉读风险章深读；若做了**采样**，必须 `log()` 说明丢了哪些章（不静默截断）。
- 单章子 agent 失败不阻断，记失败记录，最终可 completed_with_errors。

## Stage 3 · 曲线聚合 REDUCE（确定性 · bash）
**bash 运行** `scripts/aggregate_curves.py`，把所有信号卡聚合成钩子 / 爽点 / 情绪曲线 + 水章率 + 掉读风险章。纯脚本，不碰原文。

## Stage 4 · 维度评分 SYNTHESIS（一个独立子 agent）
派**一个独立子 agent**：它的上下文只有「开局卡 + Stage 3 曲线 + 可选摘要」（**不给原文全书**）+ 注入立场声明的 `references/prompt-维度评分.md`，对 6 维各给 0-100（按 `references/rubric.md` 四档 + `references/weights.json`；`rubric.md` 不可读 → 用其内置 embedded fallback，报 Rubric Source: embedded fallback）。产出按 `schemas/synthesis.schema.json` 校验。

- 总分：**bash 运行** `scripts/compute_score.py` + `scripts/load_rubric.py`，按平台权重算 weighted_total 与 grade，覆盖 judge 自填值。

## Stage 4.5 · 反调（一个独立子 agent）
派**一个独立子 agent**用 `references/prompt-反调.md` 抓过度乐观并二次道德 scrub；再 **bash 运行** `scripts/scan_moral_drift.py` 兜底删除漏网道德 finding（hard_issues + dimensions[].rationale）。

## Stage 5 · 出报告（确定性）
按 `references/报告模板.md` 生成，落盘 `评分/{书名}_商业评分.md`。开头元数据 key 用 **bash 运行** `scripts/validate_report.py` 自检齐全。

## 参考资料
| 文件 | 用途 |
|---|---|
| references/立场声明.md | 商业中立注入源 |
| references/rubric.md · references/weights.json | 6 维锚点 + 平台权重 |
| references/prompt-开局深读.md · references/prompt-逐章信号.md · references/prompt-维度评分.md · references/prompt-反调.md | 各阶段 portable prompt（子 agent 用） |
| references/报告模板.md | 输出模板 |
| schemas/signal_card.schema.json · schemas/synthesis.schema.json | 输出契约 |
| scripts/detect_chapters.py · scripts/aggregate_curves.py · scripts/compute_score.py · scripts/scan_moral_drift.py · scripts/validate_output.py · scripts/load_rubric.py · scripts/validate_report.py | 确定性数据处理（bash 运行） |

> `run_score.py` 把 Stage 0-4.5 写成固定代码（切章→逐章调用→聚合→评分→道德兜底），插入 `llm_call` 即用；scripts/*.py 是模型无关的纯 Python，依赖见 requirements.txt。
