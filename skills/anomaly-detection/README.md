# anomaly-detection — 异常检测技能

基于回归预测偏差 + 3σ 工程判据，判断指定时段是否存在束流异常。

## 包含工具

| 工具 | 说明 |
|------|------|
| `detect_anomaly` | 使用 RF 回归模型预测 + 正常工况统计分布判异 |

## 实现

- 代码：[tools/anomaly_detection.py](../../tools/anomaly_detection.py)
- 模型：[models/RF_regressor.pkl](../../models/), [models/normal_stats.npy](../../models/)

## 详细文档

见 [SKILL.md](SKILL.md)。

## 前置条件

建议先通过 `query_beam_data` 确认数据存在，再进行异常检测。
