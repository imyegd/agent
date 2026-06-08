# experiment/data — 实验数据集

存放 RAG 检索实验用的问答数据集和评估结果。

## 典型文件

| 文件 | 说明 |
|------|------|
| `qa_dataset.json` | 完整问答数据集 |
| `qa_dataset_test.json` | 测试子集（`run_experiment.py` 默认加载） |

## 数据格式

每条记录包含：

```json
{
  "question": "检索用的问题",
  "answer": "参考答案",
  "source_chunk": "标签 chunk 文本或 ID",
  "chunker_type": "fixed",
  "metadata": { ... }
}
```

## 生成方式

```bash
python experiment/generate_questions.py
```

从 `knowledge/data/` 中的文档片段，通过 LLM 自动生成问题-答案对。

## 使用

由 `experiment/evaluate_chunkers.py` 和 `experiment/run_experiment.py` 读取，不直接被 Agent 调用。
