# webnovel-score · 网文商业评分

给**长篇中文网络小说**判「商业潜力 / 签约概率」的评分工具。视角是**平台责编 + 目标读者**，只判会不会火、会不会签、能不能追读，**不做文学/道德/价值观评判**。

三条设计约束贯穿全程：

- **独立**：不依赖任何特定 agent 框架，是一套自带的 prompt + 脚本 + 契约。
- **模型无关**：确定性计算是纯 Python（零 LLM 调用）；判断部分是可移植的 prompt 文本，喂给**任意** LLM（本仓库即用于 hermes + Kimi K2.7 测试）。
- **商业中立**：合法范围内迎合网文主流的写法（男凝/慕强/后宫/虐渣/金手指…）是**商业加分项**，禁止因道德理由扣分。见 [`references/立场声明.md`](references/立场声明.md)。

---

## 核心思路：混合深度 map-reduce

长篇装不进任何 LLM 的上下文，所以**没有任何单元读整本书**：

| 内容 | 谁读 | 上下文规模 |
|---|---|---|
| 开局（前 6→10 章） | LLM 读**全文** → 开局评分卡 | 装得下 |
| 其余每一章 | LLM 每章**只读该章** → 信号卡（可并行/顺序） | 1 章 |
| 全书维度判断 | LLM **只读压缩产物**（曲线 + 开局卡） | 压缩后装得下 |

全书的「记忆」存在落盘的信号与曲线里，不存在某个单元的上下文里。**峰值上下文 = 一章大小，与书长无关。**

---

## 目录结构

```
SKILL.md                      # 编排说明：Stage 0-5 全流程 + 降级规则 + 元数据契约
references/
  立场声明.md                 # 商业中立声明（注入每个评分 prompt，唯一权威）
  rubric.md                   # 6 维锚定分档（人读）
  weights.json                # 平台→维度权重（机器读）：fanqie / qidian / zhihu / generic
  prompt-开局深读.md          # Stage 1 prompt
  prompt-逐章信号.md          # Stage 2 prompt（内嵌 signal_card 契约）
  prompt-维度评分.md          # Stage 4 prompt（内嵌 synthesis 契约 + 数量≠质量硬约束）
  prompt-反调.md              # Stage 4.5 prompt
  报告模板.md                 # Stage 5 输出模板
schemas/
  signal_card.schema.json     # Stage 2 每章输出契约（JSON Schema Draft-07）
  synthesis.schema.json       # Stage 4 输出契约
scripts/                      # 确定性纯 Python（零 LLM 调用）
  detect_chapters.py          # 切章
  aggregate_curves.py         # 曲线聚合
  compute_score.py            # 加权总分 + 评级
  scan_moral_drift.py         # 道德漂移机械兜底
  load_rubric.py              # 读平台权重
  validate_output.py          # 校验 signal_card / synthesis
  validate_report.py          # 校验报告元数据
  eval_calibration.py         # 校准 + 立场回归验收
tests/                        # 49 个 pytest（不参与运行时，只保质量）
CALIBRATION.md                # 发布前人工校准记录（含已跑的冒烟结果）
requirements.txt              # jsonschema>=4.0
```

---

## 运行流程（编排方要做的事）

每个 Stage 的**确定性部分直接跑脚本，判断部分把 prompt 发给 LLM**。数据在两者之间以 JSON 流动，过 schema 校验。

| Stage | 名称 | 执行 | 输入 → 输出 |
|---|---|---|---|
| 0 | 切章 | 脚本 `detect_chapters` | 原文 → 章节边界表 |
| 1 | 开局深读 | **LLM** `prompt-开局深读` | 前 6-10 章全文 → 开局评分卡 |
| 2 | 逐章信号 map | **LLM** `prompt-逐章信号`（每章一次） | 单章原文 → 信号卡（过 `signal_card.schema`） |
| 3 | 曲线聚合 reduce | 脚本 `aggregate_curves` | 全部信号卡 → 钩子/爽点/情绪曲线 + 水章率 + 掉读风险章 |
| 4 | 维度评分 | **LLM** `prompt-维度评分` + 脚本 `compute_score` | 开局卡+曲线 → 6 维分（过 `synthesis.schema`）；脚本按权重算总分+评级 |
| 4.5 | 反调 | **LLM** `prompt-反调` + 脚本 `scan_moral_drift` | 抓过度乐观 + 二次道德 scrub |
| 5 | 出报告 | 脚本 `validate_report` + `报告模板` | → `评分/{书名}_商业评分.md` |

### ⚠️ 关键：`{{立场声明}}` 注入（每个 LLM prompt 都要做）

四个 prompt 文件的**首行都是 `{{立场声明}}`**。发给 LLM 之前，**必须**把它替换成 `references/立场声明.md` 的**全文**。这是商业中立的注入点——不替换，模型就会退回主流道德评判，正是本工具要消除的失败模式。

```
prompt_to_send = prompt_file_text.replace(
    "{{立场声明}}",
    read("references/立场声明.md")
)
```

---

## 在 hermes + Kimi K2.7 上跑

模型无关就体现在这里：**脚本照常跑，prompt 换成发给 Kimi 即可。**

**确定性脚本**（从包根 import，Python 3.10+）：

```python
from scripts.detect_chapters import detect_chapters
from scripts.aggregate_curves import aggregate
from scripts.compute_score import compute_overall
from scripts.load_rubric import load_weights, DIMENSIONS
from scripts.validate_output import validate_signal_card, validate_synthesis
from scripts.scan_moral_drift import scan_moral_findings, scan_dimension_rationales

chapters = detect_chapters(open("book.txt", encoding="utf-8").read())
# … 每章调 Kimi 拿 signal card …
errs = validate_signal_card(card)          # 空列表 = 合规
curves = aggregate(signal_cards)           # dict：曲线 + filler_rate + dropout_risk_chapters
# … 调 Kimi 拿 synthesis（6 维分）…
dim_scores = {d["key"]: d["score"] for d in synthesis["dimensions"]}
overall = compute_overall(dim_scores, load_weights("fanqie"))  # {"weighted_total":88,"grade":"S"}
```

**每次 Kimi 调用**：`{{立场声明}}` 已注入的 prompt + 原文/压缩产物 → 要求 Kimi **只返回 JSON**（不带 code fence）→ 用对应 `validate_*` 校验，不合规就重试。Kimi 护栏与 Claude 不同，立场声明**每个 prompt 都要注入**、且 `scan_moral_drift` 作为机械兜底二次过滤——这层跨模型尤其重要。

**最小验收**（脚本层，0 LLM）：

```python
from scripts.eval_calibration import assert_calibration, stance_clean
assert_calibration(baokuan_synth, pujie_synth, margin=10)  # 爆款总分 - 扑街 ≥ 10
stance_clean(synth)   # hard_issues + dimensions[].rationale 无道德漂移 → True
```

---

## 评分维度与输出

6 个维度，每维 0-100（LLM 按 `rubric.md` 锚点整体判，附证据引用），权重按平台可调：

| 维度 | fanqie 默认权重 |
|---|---|
| 开局抓力 | 30 |
| 爽点系统 | 20 |
| 追读钩子 | 15 |
| 节奏与留存 | 15 |
| 题材卖点 | 12 |
| 长线承载 | 8 |

- **总分** = Σ(维度分 × 权重) / 100（脚本按四舍五入算，非 LLM 自填）。
- **评级**：S ≥ 85 / A 75-84 / B 60-74 / C < 60。
- **平台**：`fanqie`（默认）/ `qidian`（抬长线、降开局）/ `zhihu`（抬开局钩子）/ `generic`；未知平台回退 `generic`。
- **报告**：总分评级 + 6 维雷达 + 签约结论 + 硬伤清单（每条挂商业机制）+ 掉读风险章。开头带元数据 key（Requested/Effective Mode、Fallback、Rubric、Rubric Source、评分范围）。

**硬约束**：每条硬伤必须归到具体商业机制（开局劝退 / 中段掉读 / 平台审核风险 / 劝退目标读者盘 / 节奏拖沓 / 钩子缺失）；挂不上的（纯道德/价值观）**不允许出现**——由立场声明第 4 条 + `scan_moral_drift.py` 双层拦截。

---

## 安装与依赖

```bash
pip install -r requirements.txt   # 仅 jsonschema>=4.0；其余为标准库
python -m pytest -v               # 49 passed（从包根运行）
```

作为 skill 安装：把 `SKILL.md` + `references/` + `scripts/` + `schemas/` 复制到你的 skill 目录（`tests/` 留在开发库）。

---

## 校准状态

已跑**开局级冒烟**（详见 [`CALIBRATION.md`](CALIBRATION.md)）：

- 斗破苍穹（爆款网文开局）**88 / S** vs 无人生还（阿加莎·传统推理）**42 / C**，区分度 **46**，`assert_calibration` 通过。
- 双方 `stance_clean=True`——低分书的硬伤全部归到商业机制，**零道德扣分**。

发布前仍需补：① 真实长篇**整本** map-reduce 端到端；② 同书重跑「方差 < 5」；③ 真实**扑街网文**对照（标定中段刻度）。

---

## License

见 [`LICENSE`](LICENSE)。所处理的小说为使用者合法持有、拥有使用权的虚构作品；本工具仅做只读的商业评估。
