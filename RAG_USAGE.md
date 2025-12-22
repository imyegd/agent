# RAG系统使用说明

## 快速开始

### 1. 离线处理（首次使用或数据更新后）

将文档放入 `knowledge/data/` 文件夹，然后运行：

```bash
python -m knowledge.offline_processor
```

或使用脚本：

```bash
python scripts/rebuild_index.py
```

**生成文件：**
- `knowledge/vector_store/faiss_index.bin` - FAISS索引
- `knowledge/vector_store/documents.pkl` - 文档内容
- `knowledge/vector_store/metadata.pkl` - 元数据

### 2. 在线检索

```python
from knowledge import OnlineRetriever

retriever = OnlineRetriever()
results = retriever.search("束流强度测量", top_k=5)

for doc, score in results:
    print(f"{score:.4f}: {doc[:100]}")
```

### 3. 供LLM使用（推荐）

```python
from knowledge import search_knowledge

result = search_knowledge("束流不稳定原因", top_k=3)
print(result['results'])
```

## 目录结构

```
knowledge/
├── data/                      # 原始文档（PDF、TXT）
├── vector_store/              # 生成的索引
│   ├── faiss_index.bin
│   ├── documents.pkl
│   └── metadata.pkl
├── parsers/                   # 文档解析器
├── chunkers/                  # 文本分块器
├── offline_processor.py       # 离线处理
├── online_retriever.py        # 在线检索
└── rag_tool.py               # RAG工具（供LLM调用）
```

## 配置选项

### 分块策略

**语义分块（推荐）**
```python
OfflineProcessor(
    chunker_type="semantic",
    max_chunk_size=800,
    min_chunk_size=100
)
```

**固定大小分块**
```python
OfflineProcessor(
    chunker_type="fixed",
    chunk_size=500,
    chunk_overlap=50
)
```

### 向量化方法

**TF-IDF（推荐，本地）**
```python
embedder_type="simple"
```

**API向量化**
```python
embedder_type="api",
api_key="your_key",
base_url="api_url"
```

## 测试

```bash
python scripts/test_retriever.py
```

## 性能

- 103个文档块
- 9个PDF + TXT文件
- 索引大小: ~400KB
- 检索速度: <10ms

## 依赖

```bash
pip install pymupdf faiss-cpu scikit-learn
```

## 常见问题

### Q: 如何添加新文档？
A: 将文档放入 `knowledge/data/`，重新运行 `python -m knowledge.offline_processor`

### Q: 支持哪些文档格式？
A: 目前支持 PDF 和 TXT

### Q: 如何调整检索质量？
A: 
1. 调整分块大小（chunk_size）
2. 使用语义分块而非固定大小
3. 增加top_k获取更多结果

