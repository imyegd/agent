# anomaly-diagnosis — 异常诊断技能

提供四种方法定位导致束流异常的关键特征变量。

## 包含工具

| 工具 | 方法 |
|------|------|
| `diagnose_by_statistical_difference` | Z-score 统计差异 |
| `diagnose_by_pls` | 偏最小二乘 (PLS) |
| `diagnose_by_shap` | SHAP 模型解释 |
| `diagnose_by_autoencoder` | 自编码器重构误差 |

## 实现

- 代码：[tools/anomaly_diagnose.py](../../tools/anomaly_diagnose.py)
- 模型：[models/](../../models/) 下各诊断模型

## 详细文档

见 [SKILL.md](SKILL.md)。

## 典型流程

```
detect_anomaly（确认异常）→ diagnose_by_*（定位特征）→ explain_diagnosis_features（解释含义）
```
