# domain-knowledge-retrieval — 领域知识检索技能

三类知识检索：诊断特征解释、变量含义查询、常规领域问答。

## 包含工具

| 工具 | 数据源 | 说明 |
|------|--------|------|
| `explain_diagnosis_features` | generation KG (Neo4j) | 解释诊断出的 feature 列表 |
| `explain_variable_meaning` | generation KG (Neo4j) | 查询单个变量含义 |
| `search_domain_knowledge` | 常规 RAG (FAISS) | 束流/加速器/微电子领域问答 |

## 实现

- 代码：[knowledge/rag_tool.py](../../knowledge/rag_tool.py)
- 图谱：[knowledge/knowledge_graph/](../../knowledge/knowledge_graph/)
- 索引：[knowledge/vector_store/](../../knowledge/vector_store/)

## 详细文档

见 [SKILL.md](SKILL.md)。

## 注意事项

- `explain_*` 工具严格使用 generation 知识图谱，不回退常规 RAG
- 需本地 Neo4j；未配置时 `search_domain_knowledge` 仍可能可用（取决于向量索引）
