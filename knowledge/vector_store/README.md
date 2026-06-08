# knowledge/vector_store — 向量存储

基于 FAISS 的向量索引存储与检索。

## 主要文件

| 文件/目录 | 说明 |
|-----------|------|
| `faiss_store.py` | `FaissVectorStore` 实现：建索引、保存、加载、检索 |
| `index/` | 各分块策略生成的索引目录 |

## 索引目录结构

```
index/
└── parent_child_api/     # Parent-Child + API Embedding 索引
    ├── faiss_index.bin
    ├── documents.pkl
    └── metadata.pkl
```

实际路径以 `.openclaw.json` 中 `dependencies.knowledge.vector_index` 为准。

## 使用示例

```python
from knowledge.vector_store.faiss_store import FaissVectorStore

store = FaissVectorStore.load("knowledge/vector_store/index/parent_child_api")
results = store.search(query_vector, top_k=5)
```

## 构建索引

离线索引由知识库处理流程生成，参见 [knowledge/README.md](../README.md) 中的离线处理步骤。

## 注意事项

- `*.bin` 索引文件较大，已在 `.gitignore` 中排除
- 更换分块策略或 embedder 后需重新构建索引
