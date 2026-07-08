# CALIBRATION — 发布前门禁（手动端到端验收）

本文件是 webnovel-score skill 的**发布前手动验收门禁**。三项检查需要真实 LLM
跑完整 skill 管道，**无法在 CI/pytest 中自动化**，因此每次发版前由人工执行并把结果
填回下方表格。自动化回归（`python -m pytest`，全 12 个 Task）已覆盖纯 Python 逻辑，
本文件只负责端到端 + 立场层面的最终校验。

> ⚠️ 未跑真实 LLM 前，下方所有「结果」列保持 `TODO`，禁止填写占位/伪造数据。

## 校验工具

三项检查复用 `scripts/eval_calibration.py`：

- `assert_calibration(baokuan, pujie, margin=10) -> bool`
  —— 爆款 `weighted_total` − 扑街 `weighted_total` ≥ `margin`（默认 10）时为 `True`。
- `stance_clean(synthesis) -> bool`
  —— `synthesis["hard_issues"]` 经 `scan_moral_drift.scan_moral_findings` 扫描后
  无道德漂移 finding 时为 `True`。

调用示例（在 package 根目录执行）：

```python
import json
from scripts.eval_calibration import assert_calibration, stance_clean

baokuan = json.load(open("path/to/爆款_synthesis.json", encoding="utf-8"))
pujie   = json.load(open("path/to/扑街_synthesis.json", encoding="utf-8"))
assert assert_calibration(baokuan, pujie, margin=10) is True   # 检查 1
assert stance_clean(json.load(open("path/to/样例_synthesis.json"))) is True  # 检查 3
```

---

## 检查 1 — 爆款显著高于扑街（区分度）

**步骤**：取 2-3 本已知爆款 + 2-3 本已知扑街，各跑一次完整 skill，收集每本的
`synthesis`（含 `weighted_total`）。对每个「爆款 × 扑街」配对调用
`assert_calibration(爆款, 扑街, margin=10)`，要求全部为 `True`。

**通过标准**：所有配对 `assert_calibration(...) is True`（爆款总分 − 扑街总分 ≥ 10）。

| 爆款书名 | 爆款总分 | 扑街书名 | 扑街总分 | 差值 | assert_calibration | 通过? |
|---------|---------|---------|---------|-----|--------------------|------|
| TODO | TODO | TODO | TODO | TODO | TODO | ☐ |
| TODO | TODO | TODO | TODO | TODO | TODO | ☐ |
| TODO | TODO | TODO | TODO | TODO | TODO | ☐ |

---

## 检查 2 — 重跑稳定性（方差 < 5）

**步骤**：同一本书用同一平台配置连续跑 2 次完整 skill，记录两次 `weighted_total`，
计算 `abs(第一次 − 第二次)`。对 2-3 本样本重复。

**通过标准**：每本 `abs(总分差) < 5`。

| 书名 | 第一次总分 | 第二次总分 | abs(差) | < 5? |
|------|-----------|-----------|---------|------|
| TODO | TODO | TODO | TODO | ☐ |
| TODO | TODO | TODO | TODO | ☐ |
| TODO | TODO | TODO | TODO | ☐ |

---

## 检查 3 — 立场回归（合法男凝/虐渣不被误判为道德问题）

**步骤**：造 1-2 段「商业上合法、但内容男凝 / 虐渣」的样例，跑 Stage 4（反调/synthesis），
把产出的 `synthesis` 喂 `stance_clean`。要求 `stance_clean(synthesis) is True`——
即 `hard_issues` 里不得出现「因为男凝/虐渣本身不道德」这类道德漂移 finding；
只有归因到合法商业机制（如平台审核风险、劝退目标读者盘、中段掉读等）的才允许保留。

**通过标准**：所有样例 `stance_clean(synthesis) is True`（无道德 finding）。

| 样例描述 | hard_issues 中道德 finding 数 | stance_clean | 通过? |
|---------|------------------------------|--------------|------|
| TODO（男凝样例） | TODO | TODO | ☐ |
| TODO（虐渣样例） | TODO | TODO | ☐ |

---

## 发版判定

- [ ] 检查 1 全部通过（爆款显著 > 扑街）
- [ ] 检查 2 全部通过（重跑方差 < 5）
- [ ] 检查 3 全部通过（立场干净，无道德漂移）
- [ ] `python -m pytest` 全绿（自动化回归）

三项手动检查 + 自动化回归全部通过后方可发版。

**执行人**：TODO
**执行日期**：TODO
**skill 版本 / commit**：TODO
