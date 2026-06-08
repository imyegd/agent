# 领域知识检索技能

## 概述
提供三类知识检索能力：诊断特征解释、变量含义查询、常规领域问答。基于 Neo4j 知识图谱和混合向量检索实现，覆盖束流设备、加速器原理、微电子工艺等领域知识。

## 适用场景
- 解释异常诊断结果中出现的特征/变量的物理含义
- 查询传感器、电源、子系统的技术细节
- 回答束流/加速器/微电子相关的专业知识问题

## 工具列表

### 1. explain_diagnosis_features
**功能**: 承接异常诊断工具的输出结果，解释诊断出的异常特征（feature1-feature34）的物理含义、所属子系统、详细参数等

**原理**: 从 generation 知识图谱直接查询节点信息，不回退到常规 RAG

**参数**:
- `feature_names` (必填): 异常特征名列表，格式为 feature1-feature34，如 ['feature4', 'feature5', 'feature6']
- `top_k` (可选): 每个特征返回的相关知识条数，默认 3（当前返回节点完整详情）

**返回结构**:
```json
{
  "success": true,
  "tool": "explain_diagnosis_features",
  "message": "从 generation 知识图谱查询到 3 个特征的详细信息",
  "summary": {
    "total_requested": 3,
    "found_count": 3,
    "not_found_count": 0
  },
  "results": [
    {
      "feature_id": "feature4",
      "variable_name": "加速电源电流",
      "type": "Variable",
      "parent_system": "加速电源系统",
      "details": { ... }
    },
    ...
  ]
}
```

**使用示例**:
- "解释一下诊断结果中的 feature4、feature5、feature6 的物理含义"
- "诊断结果里 feature11、feature12 代表什么？"

**典型调用链路**: 
`detect_anomaly` → `diagnose_by_*` → `explain_diagnosis_features(top_features)`

---

### 2. explain_variable_meaning
**功能**: 解释单个变量的含义和用法

**原理**: 支持中文变量名、featureN 编号、或自然语言问题，通过知识图谱查询或关键词模糊匹配返回相关信息

**参数**:
- `query` (必填): 查询文本，可以是变量名（'加速电源电压'）、featureN（'feature3'）或问题（'加速电源电压是什么'）
- `top_k` (可选): 返回结果数量上限，默认 3

**返回结构**:
```json
{
  "success": true,
  "tool": "explain_variable_meaning",
  "message": "从 generation 知识图谱找到 1 个相关变量",
  "summary": {"matched_count": 1},
  "results": [
    {
      "match_type": "exact_variable_name",
      "feature_id": "feature6",
      "variable_name": "灯丝电源电流",
      "type": "Variable",
      "parent_system": "灯丝电源系统",
      "details": { ... }
    }
  ]
}
```

**匹配策略**（按优先级）:
1. 直接匹配 featureN 格式（如 "feature6"）
2. 直接匹配中文变量名（如 "灯丝电源电流"）
3. jieba 分词后关键词模糊搜索

**使用示例**:
- "灯丝电源电流是什么意思？"
- "feature6 是什么意思？"
- "加速电源是什么？"

---

### 3. search_domain_knowledge
**功能**: 从常规知识库检索束流、加速器、微电子设备相关的专业知识

**原理**: 使用混合检索（TF-IDF + 向量语义）从文档知识库中检索相关知识片段

**参数**:
- `query` (必填): 查询问题，如'束流强度的测量方法'、'加速器真空系统的作用'
- `top_k` (可选): 返回结果数量，默认 5
- `doc_type` (可选): 文档类型过滤（预留参数）

**返回结构**:
```json
{
  "success": true,
  "tool": "search_domain_knowledge",
  "message": "从知识库检索到 5 条相关知识",
  "summary": {
    "retrieved_count": 5,
    "index_path": "knowledge/vector_store/index/parent_child_api"
  },
  "results": [
    {"content": "...", "score": 0.87, "source": "hybrid_retriever"},
    ...
  ]
}
```

**使用示例**:
- "束流强度如何测量？"
- "离子注入工艺的原理"
- "加速器的工作原理是什么？"

---

## Feature 映射表

| Feature ID | 变量名称 | 所属系统 |
|------------|----------|----------|
| feature1 | 抑制电源电压 | 抑制电源系统 |
| feature2 | 抑制电源电流 | 抑制电源系统 |
| feature3 | 加速电源电压 | 加速电源系统 |
| feature4 | 加速电源电流 | 加速电源系统 |
| feature5 | 灯丝电源电压 | 灯丝电源系统 |
| feature6 | 灯丝电源电流 | 灯丝电源系统 |
| feature7 | 引出电源电压 | 引出电源系统 |
| feature8 | 引出电源电流 | 引出电源系统 |
| feature9 | C1 电源电压 | 电容器组系统 |
| feature10 | C2 电源电压 | 电容器组系统 |
| feature11 | C2 电源电流 | 电容器组系统 |
| feature12 | C3 电源电压 | 电容器组系统 |
| feature13 | C3 电源电流 | 电容器组系统 |
| feature14-21 | 对中/倾斜电源 | 对中调整系统 |
| feature22-29 | 消像散电流 | 消像散系统 |
| feature30 | 微调焦电流 | 聚焦系统 |
| feature31-32 | 工件台位置 X/Y | 工件台系统 |
| feature33 | 冷水机压力 | 冷却系统 |
| feature34 | 冷水机内部温度 | 冷却系统 |

## 调用时机建议
- **explain_diagnosis_features**: 仅当 diagnose_by_* 工具返回了 top_features 后，且用户要求进一步解释时使用
- **explain_variable_meaning**: 用户直接询问某个变量/feature 的含义时
- **search_domain_knowledge**: 用户提出通用的束流/加速器/微电子领域知识问题时

**注意**: 对于与业务无关的问题（如天气、菜谱、生活建议等），不应调用任何工具，直接回复说明无法处理即可。

## 依赖文件
- 知识图谱：Neo4j database="generation" (bolt://localhost:7687)
- 向量索引：`D:\code\graduate\llm\knowledge\vector_store\index\parent_child_api`
- 工具源码：`D:\code\graduate\llm\knowledge\rag_tool.py`
- Feature 映射：硬编码在 rag_tool.py 的 FEATURE_MAPPING 中

## 注意事项
- Generation KG 依赖 Neo4j 服务正常运行，如果连接失败需返回明确错误提示
- 常规 RAG 依赖向量索引存在，如果索引未构建需提示用户
- 三种工具有明确分工，不要混用：诊断特征解释走 KG，通用知识问答走 RAG
