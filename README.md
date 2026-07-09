# webnovel-score · 网文商业评分

> 模型无关的**中文网络小说商业潜力评分器**。目标读者 + 平台责编视角，判「会不会火、会不会签、能不能追读」——**不做文学 / 道德 / 价值观评判**。

给长篇中文网文打一个**商业潜力总分 + 评级（S/A/B/C）+ 6 维拆分 + 硬伤清单**。合法范围内迎合网文主流的写法（男凝 / 慕强 / 后宫 / 虐渣 / 金手指…）在这里是**商业加分项**，不会因「政治不正确 / 男凝 / 价值观」被扣分——这正是它和通用大模型直接打分最大的区别。

---

## 为什么不一样

- **商业中立（核心）** — 一段强制注入的[立场声明](references/立场声明.md) + 一层确定性[机械兜底](scripts/scan_moral_drift.py)，双层拦截模型的道德漂移。跨模型尤其重要：不同 LLM 护栏强弱不同，通用模型常把「迎合网文爽感」误判为缺陷。
- **模型无关** — 确定性计算是纯 Python（零 LLM 调用）；判断部分是可移植的 prompt 文本，喂给**任意** LLM（Claude / Kimi / GPT / 本地模型皆可）。
- **长篇不爆上下文** — 混合深度 map-reduce：开局全读 + 逐章信号 + 压缩聚合，**峰值上下文 = 一章大小，与书长无关**。
- **自包含** — 一个文件夹（SKILL.md + prompts + 脚本 + schema），不依赖任何 agent 框架。

---

## 如何工作（30 秒）

没有任何单元读整本书；全书「记忆」存在落盘的信号与曲线里：

| Stage | 谁执行 | 输入 → 输出 |
|---|---|---|
| 0 切章 | 脚本 | 原文 → 章节边界 |
| 1 开局深读 | **LLM** | 前 6-10 章全文 → 开局评分卡 |
| 2 逐章信号 map | **LLM**（按上下文预算分批，90 章≈几批） | 一批连续章节 → 每章信号卡 + 批次剧情摘要（过 schema） |
| 3 曲线聚合 reduce | 脚本 | 信号卡 → 钩子/爽点/情绪曲线 + 掉读风险章 |
| 3.5 抽查深读 | **LLM** | 中后段抽 2-3 章全文 → 核验信号卡 + 爽点执行质量证据 |
| 4 维度评分 | **LLM** + 脚本 | 开局卡+曲线 → 6 维分；脚本算总分+评级 |
| 4.5 反调 | **LLM** + 脚本 | 抓过度乐观 + 二次道德 scrub |
| 5 出报告 | 脚本 | → `评分/{书名}_商业评分.md` |

> **关键**：四个 prompt 文件首行都是 `{{立场声明}}`，发给模型前**必须**替换成 [`references/立场声明.md`](references/立场声明.md) 全文。`run_score.py` 已自动处理。

---

## 安装

### 通用（先做这一步）

```bash
git clone https://github.com/ZiliCai/webnovel-score.git
cd webnovel-score
pip install -r requirements.txt        # 仅 jsonschema>=4.0，其余标准库；Python 3.10+
python -m pytest -q                    # 49 passed，验证环境
```

一个 skill = `SKILL.md` + `references/` + `scripts/` + `schemas/` 四件套（`tests/` 仅供开发，安装时不需要）。

### Claude Code

```bash
mkdir -p ~/.claude/skills/webnovel-score
cp -R SKILL.md references scripts schemas requirements.txt ~/.claude/skills/webnovel-score/
```

重启会话后触发：`/网文评分`、`/商业评分`，或「这书能签吗」「帮我打个分」。项目级则放 `.claude/skills/`。

### OpenCode

OpenCode 原生读同一套 `SKILL.md` 格式。把上面四件套放进 OpenCode 的 skill 目录（项目级 `.opencode/skill/webnovel-score/` 或全局配置目录，**具体路径以你的 OpenCode 版本文档为准**）。可选斜杠命令：

```bash
cp adapters/opencode/command/webnovel-score.md .opencode/command/
```

### Hermes / 任意 harness / 纯 Python（编排式）

不走「skill 目录发现」机制的平台（如 Hermes + Kimi），用参考编排器 [`run_score.py`](run_score.py)，插入你自己的 `llm_call` 即可——这条路适用于**任何能跑 Python 且能调一个模型**的环境：

```python
from run_score import score_book

def llm_call(prompt: str) -> str:      # 接你的 harness / 模型；评分 prompt 需返回 JSON
    return my_model.generate(prompt)   # 例如 Kimi K2.7

result = score_book(open("book.txt", encoding="utf-8").read(),
                    llm_call, platform="fanqie", book_name="某本书")
print(result["weighted_total"], result["grade"])   # 88 S
print(result["_moral_drift_flagged"])               # 应为 []；非空=模型出现道德漂移
```

`run_score.py` 自动完成 `{{立场声明}}` 注入、逐 Stage 编排、schema 校验+重试、道德兜底。scripts/* 永不调用 LLM，模型接入点只有你传的 `llm_call`。

---

## 评分维度与输出

6 维各 0-100（LLM 按 [`rubric.md`](references/rubric.md) 锚点整体判、附证据），权重按平台可调：

| 维度 | fanqie | qidian | zhihu |
|---|---|---|---|
| 开局抓力 | 30 | 25 | 32 |
| 爽点系统 | 20 | 18 | 20 |
| 追读钩子 | 15 | 15 | 20 |
| 节奏与留存 | 15 | 14 | 14 |
| 题材卖点 | 12 | 13 | 10 |
| 长线承载 | 8 | 15 | 4 |

- **总分** = Σ(维度分 × 权重) / 100（脚本四舍五入，非模型自填）。**评级** S ≥ 85 / A 75-84 / B 60-74 / C < 60。
- **平台**：`fanqie`（默认）/ `qidian`（抬长线）/ `zhihu`（抬开局钩子）/ `generic`；未知平台回退 `generic`。
- **硬伤**：每条必须挂商业机制（开局劝退 / 中段掉读 / 平台审核风险 / 劝退目标读者盘 / 节奏拖沓 / 钩子缺失）；挂不上的纯道德条目被两层拦截，不允许出现。

---

## 商业中立立场（这是重点）

工具存在的意义就是**不替你做道德审查**。四条硬规则（[全文](references/立场声明.md)，注入每个评分 prompt）：

1. 评分者是**目标读者盘 + 平台责编**，不是文学评论家或社会评论者。
2. 男凝 / 慕强 / 后宫 / 虐渣 / 灰色主角 / 金手指等合法迎合写法 = 商业构件，执行到位即加分。
3. 唯一的内容风险口径：只有归到具体商业机制（①触发平台审核下架 ②劝退目标读者盘）才算风险。
4. 输出前删除一切「男凝 / 物化 / 价值观 / 进步 / 爹味」类、又不能归因到商业机制的评判。

脚本层 [`scan_moral_drift.py`](scripts/scan_moral_drift.py) 对 `hard_issues` 和 `dimensions[].rationale` 双双做机械兜底——即使某个模型没守住立场，漂移条目也会被拦下（`run_score` 会把它们放进 `_moral_drift_flagged`）。

---

## 目录结构

```
SKILL.md            编排说明（Stage 0-5 + 降级规则 + 元数据契约）
run_score.py        参考编排器（平台/模型无关，插 llm_call 即用）
references/         立场声明 · rubric · weights.json · 4×prompt · 报告模板
schemas/            signal_card / synthesis 输出契约（JSON Schema）
scripts/            9 个纯 Python：切章/聚合/算分/道德扫描/校验/loader/校准
adapters/opencode/  OpenCode 斜杠命令包装
tests/              49 个 pytest（仅开发用）
CALIBRATION.md      发布前人工校准记录（含冒烟结果）
```

---

## 校准状态

已跑**开局级冒烟**（详见 [CALIBRATION.md](CALIBRATION.md)）：斗破苍穹（爆款）**88/S** vs 无人生还（传统推理）**42/C**，区分度 46，双方 `stance_clean=True`、零道德扣分。

发布前仍需补：① 真实长篇**整本**端到端；② 同书重跑「方差 < 5」；③ 真实**扑街网文**对照。

---

## 贡献

欢迎 issue / PR：新增平台适配（`adapters/`）、rubric 权重调优、扑街对照样本、新平台 rubric。改动请保持三条约束不破——独立、模型无关、商业中立——并让 `python -m pytest` 全绿。

## License

见 [LICENSE](LICENSE)。所处理的小说为使用者合法持有、拥有使用权的虚构作品；本工具仅做只读的商业评估。
