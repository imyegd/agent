# experiment/plot — 实验图表

存放 RAG 检索实验的可视化输出脚本和生成图表。

## 脚本

| 脚本 | 说明 |
|------|------|
| `plot_chunker_results.py` | 分块策略对比图 |
| `plot_retriever_results.py` | 检索器对比图 |
| `plot_kgfusion_results.py` | 知识图谱融合检索对比图 |

## 使用

实验评估完成后运行对应脚本：

```bash
python experiment/plot/plot_chunker_results.py
```

## 输出

图表以 PNG 格式保存在本目录，用于论文/报告中的检索效果对比展示。

## 数据来源

读取 `experiment/data/` 中的评估结果 JSON，由 `evaluate_chunkers.py` 生成。
