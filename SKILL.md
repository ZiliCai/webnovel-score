---
name: webnovel-score
version: 0.1.0
description: "长篇网文商业潜力/签约概率评分。独立、模型无关、商业中立（目标读者+平台责编视角，不做道德评判）。混合深度 map-reduce：开局全读+逐章信号+压缩聚合+holistic judge。触发：/网文评分、/商业评分、「这书能签吗」「打个分」。"
---
# webnovel-score：网文商业评分

判长篇网文的商业潜力/签约概率。独立、模型无关、商业中立。

## 立场（最高优先）
每个评分类 prompt 运行前，把 `references/立场声明.md` 全文替换进该 prompt 的 `{{立场声明}}` 占位。禁止任何道德/价值观理由扣分或产生 finding——见立场声明第 4 条，并由 `scripts/scan_moral_drift.py` 机械兜底。

## Stage 0 · 定位切章
1. 确认书名/原文路径/目标平台。
2. **自适应快路**：同目录若有 `拆文库/{书名}/` 章节摘要，直接读来替代 Stage 2 提取（可选、纯读文件）；无则继续。
3. 用 `scripts/detect_chapters.py` 切章，得边界表。识别不到 → 请用户确认格式。

## Stage 1 · 开局深读
读前 6 章全文（前 6 章内无首爽或核心钩子则延到前 10 章封顶；不足 6 章全读），用 `references/prompt-开局深读.md` 产开局评分卡。

## Stage 2 · 逐章信号 MAP
对其余每章用 `references/prompt-逐章信号.md` 产信号卡，按 `schemas/signal_card.schema.json` 用 `scripts/validate_output.py` 校验。
- **并行/降级**：harness 支持子任务则批 5-8 并行；不支持或已在子代理内 → 顺序分批（Effective Mode: sequential），语义一致。
- **大书(>200 章)**：钩子/爽点用便宜模型全量扫，仅对曲线标出的掉读风险章深读；若采样必须 `log()` 说明丢了哪些章（不静默截断）。
- 单章失败不阻断，记失败记录，最终可 completed_with_errors。

## Stage 3 · 曲线聚合 REDUCE
用 `scripts/aggregate_curves.py` 把信号卡聚合成钩子/爽点/情绪曲线 + 水章率 + 掉读风险章。纯脚本，不碰原文。

## Stage 4 · 维度评分 SYNTHESIS
用 `references/prompt-维度评分.md` 读「开局卡+曲线+可选摘要」给 6 维 0-100（按 `references/rubric.md` 四档 + `references/weights.json`；rubric.md 不可读 → 用其内置 embedded fallback，报 Rubric Source: embedded fallback）。产出按 `schemas/synthesis.schema.json` 校验。
- 总分：用 `scripts/compute_score.py` + `scripts/load_rubric.py` 按平台权重算 weighted_total 与 grade，覆盖 judge 自填值。

## Stage 4.5 · 反调
用 `references/prompt-反调.md` 抓过度乐观并二次道德 scrub；再跑 `scripts/scan_moral_drift.py` 兜底删除漏网道德 finding。

## Stage 5 · 出报告
按 `references/报告模板.md` 生成，落盘 `评分/{书名}_商业评分.md`。开头元数据 key 用 `scripts/validate_report.py` 自检齐全。

## 参考资料
| 文件 | 用途 |
|---|---|
| references/立场声明.md | 商业中立注入源 |
| references/rubric.md · references/weights.json | 6 维锚点 + 平台权重 |
| references/prompt-开局深读.md · references/prompt-逐章信号.md · references/prompt-维度评分.md · references/prompt-反调.md | 各阶段 portable prompt |
| references/报告模板.md | 输出模板 |
| schemas/signal_card.schema.json · schemas/synthesis.schema.json | 输出契约 |
| scripts/detect_chapters.py · scripts/aggregate_curves.py · scripts/compute_score.py · scripts/scan_moral_drift.py · scripts/validate_output.py · scripts/load_rubric.py · scripts/validate_report.py | 确定性数据处理 |
