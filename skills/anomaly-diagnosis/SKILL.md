# 异常诊断技能

## 概述
提供四种不同的异常特征诊断方法，用于定位导致束流异常的关键变量。每种方法基于不同的原理和假设，可以通过一致性对比提高诊断结果的可靠性。

## 适用场景
- 已检测到异常时段，需要定位具体原因
- 分析哪些传感器/变量对异常贡献最大
- 不同诊断方法结果对比验证

## 工具列表

### 1. diagnose_by_statistical_difference
**功能**: 基于统计差异（Z-score）的异常特征诊断方法

**原理**: 对比异常时间段与正常时间段内各变量的统计分布差异，识别发生显著偏移的关键变量。

**参数**:
- `anomaly_start` (必填): 异常时段起始时间
- `anomaly_end` (必填): 异常时段结束时间
- `normal_start` (必填): 正常时段起始时间（作为统计基准）
- `normal_end` (必填): 正常时段结束时间
- `top_k` (可选): 返回偏移最显著的前 k 个特征，默认 10

**返回结构**:
```json
{
  "method": "statistical_difference",
  "anomaly_range": ["2025-08-30 20:00:00", "2025-08-30 21:00:00"],
  "top_features": [
    {"feature": "feature4", "z_score": 3.45},
    {"feature": "feature6", "z_score": 2.87},
    ...
  ]
}
```

**使用示例**:
- "用统计差异方法诊断 2025-08-30 20:00:00 到 21:00:00 的异常，正常时段取 2025-08-30 18:00:00 到 19:00:00"

---

### 2. diagnose_by_pls
**功能**: 基于已训练的 PLS 模型权重的异常特征诊断

**原理**: 通过偏最小二乘模型中各输入变量对目标束流的线性投影权重，识别与束流变化高度相关的关键变量。

**参数**:
- `anomaly_start` (必填): 异常时段起始时间
- `anomaly_end` (必填): 异常时段结束时间
- `top_k` (可选): 返回权重最大的前 k 个特征，默认 10

**返回结构**:
```json
{
  "method": "pls",
  "anomaly_range": ["...", "..."],
  "top_features": [
    {"feature": "feature3", "pls_weight": 0.85},
    {"feature": "feature7", "pls_weight": 0.62},
    ...
  ]
}
```

**使用示例**:
- "用 PLS 方法诊断 2025-08-30 18:00:00 到 19:00:00 的异常特征"

---

### 3. diagnose_by_shap
**功能**: 基于 SHAP 方法的异常特征诊断

**原理**: 对已训练的回归模型进行解释，分析异常时段内各变量对模型预测结果的贡献程度。

**参数**:
- `anomaly_start` (必填): 异常时段起始时间
- `anomaly_end` (必填): 异常时段结束时间
- `model_name` (可选): 使用的回归模型，可选 'RF'/'XGB'/'LGBM'/'MLP'/'Linear'，默认 'RF'
- `top_k` (可选): 返回 SHAP 重要性最高的前 k 个特征，默认 10

**返回结构**:
```json
{
  "method": "shap",
  "model": "RF",
  "anomaly_range": ["...", "..."],
  "top_features": [
    {"feature": "feature5", "mean_abs_shap": 12.34},
    {"feature": "feature11", "mean_abs_shap": 8.92},
    ...
  ]
}
```

**使用示例**:
- "用 SHAP 方法诊断 2025-08-30 18:00:00 到 19:00:00 的异常，用随机森林模型"
- "SHAP 分析 2025-08-30 22:00:00 到 23:00:00，用 LightGBM"

---

### 4. diagnose_by_autoencoder
**功能**: 基于自编码器重构误差的异常特征诊断

**原理**: 通过分析异常时段内各变量的重构误差，识别相对于正常工况分布发生显著偏离的关键变量。无需监督标签。

**参数**:
- `anomaly_start` (必填): 异常时段起始时间
- `anomaly_end` (必填): 异常时段结束时间
- `top_k` (可选): 返回重构误差最大的前 k 个特征，默认 10

**返回结构**:
```json
{
  "method": "autoencoder",
  "anomaly_range": ["...", "..."],
  "top_features": [
    {"feature": "feature2", "mean_reconstruction_error": 0.035},
    {"feature": "feature9", "mean_reconstruction_error": 0.028},
    ...
  ]
}
```

**使用示例**:
- "用自编码器诊断 2025-08-30 18:00:00 到 19:00:00 的异常特征"

---

## 方法选择建议

| 方法 | 适用场景 | 优点 | 局限 |
|------|----------|------|------|
| 统计差异 | 有明确的正常工况参考时段 | 简单直观，易解释 | 依赖正常时段的选取 |
| PLS | 已知变量间存在线性关系 | 考虑变量间相关性 | 对非线性关系敏感 |
| SHAP | 需要模型级别的解释 | 可解释性强，支持多种模型 | 计算成本较高 |
| AutoEncoder | 无监督场景 | 不依赖标注数据 | 需要足够多的正常样本训练 |

## 调用时机建议
- 在检测到异常后（detect_anomaly 返回 is_anomaly=true）调用
- 可以根据需求同时调用多种方法进行对比
- 诊断结果后可调用 explain_diagnosis_features 进一步理解异常特征的含义

## 依赖文件
- 数据文件：`D:\code\graduate\llm\data\束流.csv`
- PLS 模型：`D:\code\graduate\llm\models\pls_model.pkl`
- SHAP 模型：`D:\code\graduate\llm\models\{RF,XGB,LGBM,MLP,Linear}_regressor.pkl`
- AutoEncoder 模型：`D:\code\graduate\llm\models\ae_model.pt`
- 工具源码：`D:\code\graduate\llm\tools\anomaly_diagnose.py`
