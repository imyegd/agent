# knowledge/retrievers — 检索器

提供多种文档检索策略，供 RAG 和混合检索使用。

## 检索器类型

| 类型 | 类名 | 说明 |
|------|------|------|
| `keyword` | `KeywordRetriever` | TF-IDF 关键词检索 |
| `vector` | `VectorRetriever` | 向量语义检索（FAISS） |
| `hybrid` | `HybridRetriever` | TF-IDF + 向量 RRF 融合 |
| `kg` | `KGRetriever` | 知识图谱检索 |
| `fusion` | `FusionRetriever` | 多路检索融合（向量 + KG） |

## 工厂方法

```python
from knowledge.retrievers.retriever_factory import RetrieverFactory

retriever = RetrieverFactory.create_retriever(
    retriever_type="hybrid",
    documents=doc_list,
    embedder_type="api"
)
results = retriever.retrieve("束流不稳定原因", top_k=5)
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `base_retriever.py` | 检索器基类 |
| `keyword_retriever.py` | TF-IDF 检索 |
| `vector_retriever.py` | 向量检索 |
| `hybrid_retriever.py` | 混合检索 |
| `kg_retriever.py` | 知识图谱检索 |
| `fusion_retriever.py` | 多路融合检索 |
| `retriever_factory.py` | 工厂入口 |

## 在 Agent 中的使用

`search_domain_knowledge` 工具通过 [rag_tool.py](../rag_tool.py) 调用混合检索器，索引路径见 `.openclaw.json` 中 `dependencies.knowledge.vector_index`。
