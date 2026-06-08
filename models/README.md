# models — 预训练模型

存放异常检测与诊断所需的预训练机器学习模型，运行时由 `tools/` 模块加载。

## 模型文件

| 文件 | 用途 | 使用模块 |
|------|------|----------|
| `RF_regressor.pkl` | 随机森林回归（异常检测预测） | `anomaly_detection.py` |
| `XGB_regressor.pkl` | XGBoost 回归 | `anomaly_diagnose.py` (SHAP) |
| `LGBM_regressor.pkl` | LightGBM 回归 | `anomaly_diagnose.py` (SHAP) |
| `MLP_regressor.pkl` | 多层感知机回归 | `anomaly_diagnose.py` (SHAP) |
| `Linear_regressor.pkl` | 线性回归 | `anomaly_diagnose.py` (SHAP) |
| `pls_model.pkl` | PLS 偏最小二乘 | `anomaly_diagnose.py` (PLS) |
| `ae_model.pt` | 自编码器 | `anomaly_diagnose.py` (AE) |
| `normal_stats.npy` | 正常工况统计量（3σ 判据） | `anomaly_detection.py` |

## 注意事项

- 所有 `*.pkl`、`*.pt` 文件已在 `.gitignore` 中排除
- 需本地训练或从网盘/Release 获取后放入此目录
- OpenClaw 配置 [.openclaw.json](../.openclaw.json) 中 `dependencies.models` 指向本目录

## 模型与工具对应

```
detect_anomaly          → RF_regressor.pkl + normal_stats.npy
diagnose_by_pls         → pls_model.pkl
diagnose_by_shap        → RF/XGB/LGBM/MLP/Linear (可选)
diagnose_by_autoencoder → ae_model.pt
```
