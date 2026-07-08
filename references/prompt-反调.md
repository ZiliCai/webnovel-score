{{立场声明}}

【任务：反调 cross-check】
你拿到一份已完成的评分。做两件事：
1. 过度乐观检查：逐维问"这个分是不是打高了？"有证据支持才下调，输出 score_adjustments。
2. 二次道德 scrub：扫 hard_issues，凡含道德/价值观评判词、又不能归因到①平台审核②劝退目标读者盘的，移除并记入 removed_moral_findings。
输出 JSON（不带 code fence）：
{
  "score_adjustments": [{"key": "维度名", "from": 旧分, "to": 新分, "reason": "依据"}],
  "removed_moral_findings": ["被删 finding 的原文"]
}
