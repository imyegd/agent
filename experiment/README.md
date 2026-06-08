# experiment — RAG 检索实验

评估不同文本分块（Chunker）策略对知识检索效果的影响。

## 实验流程

```bash
python experiment/run_experiment.py
```

自动化执行：

1. 加载问答数据集（`experiment/data/`）
2. 分别用 fixed / semantic / chapter 等分块策略构建索引
3. 评估检索准确率（是否命中标签 chunk）
4. 生成对比报告与图表（`experiment/plot/`）

## 主要脚本

| 脚本 | 说明 |
|------|------|
| `run_experiment.py` | 完整实验入口 |
| `generate_questions.py` | 从文档片段生成 QA 数据集 |
| `evaluate_chunkers.py` | 分块策略检索效果评估 |
| `compare_parent_child_methods.py` | Parent-Child 分块对比 |

## 子目录

| 目录 | 说明 |
|------|------|
| [data/](data/README.md) | 问答数据集与评估结果 JSON |
| [plot/](plot/README.md) | 实验对比图表输出 |

## 实验参数

通过 `run_experiment.py` 命令行参数配置：

- `num_fragments`：文本片段数量
- `questions_per_fragment`：每片段生成问题数
- `chunker_types`：分块策略列表
- `embedder_type`：`api` 或 `simple`（TF-IDF）
- `top_k`：检索返回条数

## 依赖

- [knowledge/](../knowledge/) 模块的 chunker、embedder、vector_store
- ModelScope Embedding API（`embedder_type=api` 时）
