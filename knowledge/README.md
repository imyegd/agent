# Knowledge RAG系统

## 架构说明

```
knowledge/
├── parsers/              # 文档解析器
│   ├── base_parser.py    # 解析器基类
│   ├── txt_parser.py     # TXT解析器
│   ├── pdf_parser.py     # PDF解析器
│   └── parser_factory.py # 解析器工厂
│
├── chunkers/             # 文本分块器
│   ├── base_chunker.py   # 分块器基类
│   ├── fixed_size_chunker.py    # 固定大小分块
│   ├── semantic_chunker.py      # 语义分块
│   └── chunker_factory.py       # 分块器工厂
│
├── vector_store/         # 向量存储
│   ├── faiss_store.py    # FAISS向量存储
│   └── faiss_index.bin   # 生成的索引文件
│
├── data/                 # 原始文档
│   ├── *.pdf
│   └── *.txt
│
├── offline_processor.py  # 离线处理器（解析、分块、索引）
├── online_retriever.py   # 在线检索器（加载索引、检索）
├── embeddings.py         # 向量化模块
├── rag_tool.py           # RAG工具（供LLM调用）
└── knowledge_base.py     # 旧版JSON知识库（兼容）
```

## 使用流程

### 1. 离线处理（一次性）

```python
from knowledge import OfflineProcessor

# 创建处理器
processor = OfflineProcessor(
    data_dir="knowledge/data",
    output_dir="knowledge/vector_store",
    chunker_type="semantic",  # 或 "fixed"
    chunk_size=500,
    chunk_overlap=50,
    embedder_type="simple"    # TF-IDF，不需要API
)

# 处理所有文档
stats = processor.process_directory()

# 生成文件:
# - knowledge/vector_store/faiss_index.bin
# - knowledge/vector_store/documents.pkl
# - knowledge/vector_store/metadata.pkl
```

或直接运行:
```bash
python -m knowledge.offline_processor
```

### 2. 在线检索

```python
from knowledge import OnlineRetriever

# 创建检索器（自动加载离线索引）
retriever = OnlineRetriever()

# 检索
results = retriever.search("束流强度测量", top_k=5)

for doc, score in results:
    print(f"Score: {score:.4f}")
    print(f"Content: {doc[:100]}...")
```

### 3. 供LLM使用（最简单）

```python
from knowledge import search_knowledge

# 直接调用
result = search_knowledge("束流不稳定原因", top_k=3)
print(result)
```

## 分块策略

### 固定大小分块 (fixed)
- 优点: 速度快，可控
- 缺点: 可能切断语义
- 适用: 文档结构不规则时

### 语义分块 (semantic) 推荐
- 优点: 保留完整语义，更符合自然段落
- 缺点: 块大小不均匀
- 适用: 规范文档、技术资料

## 向量化方法

### Simple (TF-IDF)
- 无需API，纯本地
- 速度快
- 适合中文文档
- **推荐用于开发测试**

### API (OpenAI/ModelScope)
- 需要API key
- 向量质量更好
- 适合生产环境

## 性能

- 103个文档块
- 9个PDF + TXT文件
- 索引大小: ~400KB
- 检索速度: <10ms

