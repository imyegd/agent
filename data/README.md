# data — 数据目录

存放束流运行数据、工具定义备份和训练样本。

## 目录结构

```
data/
├── 束流.csv              # 主数据集（时间序列 + target + feature1-34）
├── tools_summary.json    # 工具 JSON Schema 备份
└── train_gen/            # 工具调用训练数据生成产物
```

## 束流.csv

主数据集，包含：

- `时间`：时间戳列
- `target`：束流强度（预测/检测目标）
- `feature1` ~ `feature34`：34 个工艺/设备相关特征变量

被 `tools/data_query.py`、`tools/anomaly_detection.py` 等模块直接读取。

## tools_summary.json

11 个工具的 Function Calling 定义备份，供训练数据生成脚本参考。

## train_gen/

工具调用微调数据的三步流水线输出目录，详见 [train_gen/README.md](train_gen/README.md)。

## 注意事项

- CSV 文件体积较大时可使用 Git LFS 或本地单独管理
- 时间范围会被 `scripts/step1_generate_questions.py` 动态读取，用于生成合理的查询问题
