# knowledge/knowledge_graph — 知识图谱

基于 Neo4j 构建和查询束流设备知识图谱，支撑变量解释与诊断特征说明。

## 数据库

| 数据库 | 用途 |
|--------|------|
| `generation` | 34 个 feature 变量、子系统、功能关系（供 `explain_*` 工具） |
| `papers` | 论文领域知识（可选） |

默认连接：`bolt://localhost:7687`，用户 `neo4j`。

## 主要脚本

| 脚本 | 说明 |
|------|------|
| `create.py` | 从 JSON 导入节点和关系到 Neo4j |
| `query.py` | 图谱查询示例（变量结构、诊断上下文） |
| `gen_relation_from_chunks.py` | 从文本块自动生成关系 |
| `gen_custom_config.py` | 自定义图谱配置生成 |

## 图谱结构示例

```
(Variable)-[:BELONGS_TO]->(Subsystem)
(Variable)-[:HAS_FUNCTION]->(Function)
(Variable)-[:MAY_AFFECT]->(Metric)
```

## 使用

Agent 通过 [rag_tool.py](../rag_tool.py) 中的 `GenerationKGQuery` 类查询，不直接调用本目录脚本。

```python
# 手动测试
python knowledge/knowledge_graph/query.py
```

## 依赖

```bash
pip install neo4j
```

需本地启动 Neo4j 服务。未配置时 `explain_diagnosis_features` 和 `explain_variable_meaning` 不可用，常规 RAG 仍可用。
