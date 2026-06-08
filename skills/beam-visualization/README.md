# beam-visualization — 束流可视化技能

绘制束流时序折线图，支持多曲线叠加和异常区域高亮。

## 包含工具

| 工具 | 说明 |
|------|------|
| `plot_beam_data` | 绘制 target 及可选特征曲线 |

## 实现

- 代码：[tools/visualization.py](../../tools/visualization.py)
- 输出：[output/](../../output/)

## 详细文档

见 [SKILL.md](SKILL.md)。

## 调用时机

仅在用户明确要求「画图」「可视化」「查看曲线」时调用，避免自动生成图表。
