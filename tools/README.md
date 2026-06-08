# tools — LLM 工具函数

本目录实现 Agent 可调用的全部工具函数，通过 OpenAI Function Calling 协议暴露给 LLM。

## 模块结构

| 文件 | 工具 | 说明 |
|------|------|------|
| `data_query.py` | `query_beam_data`, `get_data_info` | CSV 数据查询与元信息 |
| `anomaly_detection.py` | `detect_anomaly` | 3σ 异常检测 |
| `anomaly_diagnose.py` | `diagnose_by_*` (4个) | 统计/PLS/SHAP/AE 诊断 |
| `visualization.py` | `plot_beam_data` | 束流时序图 |
| `__init__.py` | — | 汇总 `TOOLS` 和 `TOOL_FUNCTIONS` |

RAG 工具定义在 [knowledge/rag_tool.py](../knowledge/rag_tool.py)，由 `__init__.py` 动态导入。

## 工具一览

| 分类 | 工具名称 | 功能描述 |
|------|----------|----------|
| 数据查询 | `query_beam_data` | 按时间范围查询束流数据 |
| 数据查询 | `get_data_info` | 获取数据集元信息 |
| 异常检测 | `detect_anomaly` | 回归预测 + 3σ 判据 |
| 异常诊断 | `diagnose_by_statistical_difference` | Z-score 统计差异诊断 |
| 异常诊断 | `diagnose_by_pls` | PLS 权重诊断 |
| 异常诊断 | `diagnose_by_shap` | SHAP 模型解释诊断 |
| 异常诊断 | `diagnose_by_autoencoder` | 自编码器重构误差诊断 |
| 可视化 | `plot_beam_data` | 束流时序图绘制 |
| 知识检索 | `explain_diagnosis_features` | 诊断特征解释（generation KG） |
| 知识检索 | `explain_variable_meaning` | 变量含义查询（generation KG） |
| 知识检索 | `search_domain_knowledge` | 领域知识检索（常规 RAG） |

## 注册方式

```python
from tools import TOOLS, TOOL_FUNCTIONS

# TOOLS: OpenAI Function Calling 格式的工具定义列表
# TOOL_FUNCTIONS: 工具名 → 可调用函数 的映射
result = TOOL_FUNCTIONS["query_beam_data"](
    start_time="2025-08-31 02:00:00",
    end_time="2025-08-31 03:00:00"
)
```

## 依赖

| 模块 | 依赖资源 |
|------|----------|
| `data_query.py` | `data/束流.csv` |
| `anomaly_detection.py` | `models/RF_regressor.pkl`, `models/normal_stats.npy` |
| `anomaly_diagnose.py` | `models/` 下各诊断模型 |
| `visualization.py` | matplotlib，输出到 `output/` |
| RAG 工具 | Neo4j + `knowledge/vector_store/` 索引 |

## 添加新工具

1. 在对应模块中实现函数并定义 JSON Schema
2. 在模块内注册到 `*_TOOLS` 和 `*_TOOL_FUNCTIONS`
3. 在 `__init__.py` 中汇总
4. 更新 [agents/llm_agent.py](../agents/llm_agent.py) 的 system prompt
5. 同步更新 [skills/](../skills/) 对应技能文档

## 详细说明

更完整的参数与返回结构见 [TOOLS_README.md](TOOLS_README.md)。
