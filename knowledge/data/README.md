# knowledge/data — 知识库原始数据

存放 RAG 知识库和知识图谱的原始文档与结构化数据。

## 子目录

| 目录 | 内容 |
|------|------|
| `papers/` | 加速器/束流相关论文 PDF 与解析文本 |
| `books/` | 专业书籍 PDF（体积大，默认不纳入 Git） |
| `generations/` | 设备变量/子系统说明（generation KG 数据源） |
| `graph/` | 知识图谱 JSON 定义（如离子注入机知识图谱） |

## 数据流

```
papers/*.pdf  ──→ parsers/ ──→ chunkers/ ──→ vector_store/
graph/*.json  ──→ knowledge_graph/create.py ──→ Neo4j
generations/  ──→ knowledge_graph/ ──→ Neo4j (generation 库)
```

## 注意事项

- `books/**/*.pdf` 在 `.gitignore` 中排除，需本地单独获取
- 新增文档后需重新运行离线索引构建（见 [knowledge/README.md](../README.md)）
- 图谱 JSON 由 `knowledge_graph/create.py` 导入 Neo4j
