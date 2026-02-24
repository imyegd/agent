"""
RAG 工具模块 - 重构版
提供三类知识检索工具：
1. 承接异常诊断结果解释（feature 列表 -> generation KG）
2. 变量含义/用法查询（自然语言或变量名 -> generation KG）
3. 常规领域问答（束流/加速器/微电子 -> 常规 RAG）
"""
from typing import Dict, Any, List, Optional
import os
import sys
import json

# 添加项目根路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("[警告] neo4j 驱动未安装，generation KG 工具将不可用")

try:
    import jieba
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False
    print("[警告] jieba 未安装，关键词提取功能受限")

# =========================
# Feature 到变量名映射（来自 tools/kg_diagnosis_explainer.py）
# =========================
FEATURE_MAPPING = {
    "feature1": "抑制电源电压",
    "feature2": "抑制电源电流",
    "feature3": "加速电源电压",
    "feature4": "加速电源电流",
    "feature5": "灯丝电源电压",
    "feature6": "灯丝电源电流",
    "feature7": "引出电源电压",
    "feature8": "引出电源电流",
    "feature9": "C1电源电压",
    "feature10": "C2电源电压",
    "feature11": "C2电源电流",
    "feature12": "C3电源电压",
    "feature13": "C3电源电流",
    "feature14": "对中X偏移电源电压",
    "feature15": "对中X偏移电源电流",
    "feature16": "对中Y偏移电源电压",
    "feature17": "对中Y偏移电源电流",
    "feature18": "对中X倾斜电源电压",
    "feature19": "对中X倾斜电源电流",
    "feature20": "对中Y倾斜电源电压",
    "feature21": "对中Y倾斜电源电流",
    "feature22": "斜向消像散1电流",
    "feature23": "斜向消像散2电流",
    "feature24": "斜向消像散3电流",
    "feature25": "斜向消像散4电流",
    "feature26": "轴向消像散1电流",
    "feature27": "轴向消像散2电流",
    "feature28": "轴向消像散3电流",
    "feature29": "轴向消像散4电流",
    "feature30": "微调焦电流",
    "feature31": "工件台位置X",
    "feature32": "工件台位置Y",
    "feature33": "冷水机压力",
    "feature34": "冷水机内部温度",
}

# 反向映射（中文名 -> featureN）
VARIABLE_TO_FEATURE = {v: k for k, v in FEATURE_MAPPING.items()}


# =========================
# Generation KG 查询器
# =========================

class GenerationKGQuerier:
    """Generation 知识图谱查询器（连接 Neo4j generation 数据库）"""
    
    def __init__(
        self,
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: str = "12345678",
        database: str = "generation"
    ):
        """
        初始化 Generation KG 查询器
        
        Args:
            neo4j_uri: Neo4j URI
            neo4j_user: 用户名
            neo4j_password: 密码
            database: 数据库名（默认 generation）
        """
        if not NEO4J_AVAILABLE:
            self.driver = None
            self.available = False
            return
        
        try:
            self.driver = GraphDatabase.driver(
                neo4j_uri,
                auth=(neo4j_user, neo4j_password)
            )
            self.database = database
            self.available = True
        except Exception as e:
            print(f"[GenerationKG] 连接失败: {e}")
            self.driver = None
            self.available = False
    
    def query_variable_by_name(self, variable_name: str) -> Optional[Dict[str, Any]]:
        """
        按变量名查询节点详细信息
        
        Args:
            variable_name: 变量名（如"加速电源电压"）
        
        Returns:
            节点信息字典或 None
        """
        if not self.available or not self.driver:
            return None
        
        def _query(tx, name):
            # 查询节点自身属性 + 所属关系
            result = tx.run("""
            MATCH (v {name: $name})
            OPTIONAL MATCH (v)-[r:属于]->(parent)
            RETURN v, labels(v) as node_type, parent.name as parent_name
            """, name=name)
            record = result.single()
            if not record:
                return None
            
            node = record["v"]
            node_type = record["node_type"][0] if record["node_type"] else "Unknown"
            parent_name = record["parent_name"]
            
            # 提取节点所有属性
            props = dict(node.items())
            
            return {
                "name": props.get("name"),
                "type": node_type,
                "parent": parent_name,
                "properties": props
            }
        
        try:
            with self.driver.session(database=self.database) as session:
                return session.execute_read(_query, variable_name)
        except Exception as e:
            print(f"[GenerationKG] 查询失败: {e}")
            return None
    
    def fuzzy_search_variables(self, keywords: List[str], limit: int = 5) -> List[Dict[str, Any]]:
        """
        按关键词模糊搜索变量节点
        
        Args:
            keywords: 关键词列表
            limit: 返回结果数量上限
        
        Returns:
            匹配节点列表
        """
        if not self.available or not self.driver:
            return []
        
        def _search(tx, kws, lim):
            # 构造模糊匹配条件（OR）
            conditions = " OR ".join([f"v.name CONTAINS '{kw}'" for kw in kws])
            query = f"""
            MATCH (v)
            WHERE {conditions}
            OPTIONAL MATCH (v)-[r:属于]->(parent)
            RETURN v, labels(v) as node_type, parent.name as parent_name
            LIMIT $limit
            """
            results = tx.run(query, limit=lim)
            
            nodes = []
            for record in results:
                node = record["v"]
                node_type = record["node_type"][0] if record["node_type"] else "Unknown"
                parent_name = record["parent_name"]
                props = dict(node.items())
                
                nodes.append({
                    "name": props.get("name"),
                    "type": node_type,
                    "parent": parent_name,
                    "properties": props
                })
            return nodes
        
        try:
            with self.driver.session(database=self.database) as session:
                return session.execute_read(_search, keywords, limit)
        except Exception as e:
            print(f"[GenerationKG] 模糊搜索失败: {e}")
            return []
    
    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()


# =========================
# 工具实现
# =========================

def explain_diagnosis_features(
    feature_names: List[str],
    top_k: int = 3
) -> Dict[str, Any]:
    """
    工具一：承接异常诊断结果，解释 feature 列表
    
    Args:
        feature_names: 异常特征名列表（如 ["feature4", "feature5", "feature6"]）
        top_k: 每个 feature 返回的相关知识条数（当前固定返回节点详情）
    
    Returns:
        统一结构化结果
    """
    if not feature_names:
        return {
            "success": False,
            "tool": "explain_diagnosis_features",
            "message": "feature_names 不能为空",
            "error": {
                "type": "invalid_input",
                "detail": "feature_names 列表为空",
                "suggestion": "请提供至少一个 feature 名称，如 ['feature4']"
            }
        }
    
    querier = GenerationKGQuerier()
    if not querier.available:
        return {
            "success": False,
            "tool": "explain_diagnosis_features",
            "message": "Generation 知识图谱不可用",
            "error": {
                "type": "kg_unavailable",
                "detail": "Neo4j 连接失败或 generation 数据库不存在",
                "suggestion": "请检查 Neo4j 服务状态和数据库配置"
            }
        }
    
    results = []
    not_found = []
    
    for feature_name in feature_names:
        # 转为中文变量名
        var_name = FEATURE_MAPPING.get(feature_name.lower())
        if not var_name:
            not_found.append(feature_name)
            continue
        
        # 查询节点
        node_info = querier.query_variable_by_name(var_name)
        if node_info:
            results.append({
                "feature_id": feature_name,
                "variable_name": var_name,
                "type": node_info.get("type"),
                "parent_system": node_info.get("parent"),
                "details": node_info.get("properties", {})
            })
        else:
            not_found.append(feature_name)
    
    querier.close()
    
    return {
        "success": True,
        "tool": "explain_diagnosis_features",
        "message": f"从 generation 知识图谱查询到 {len(results)} 个特征的详细信息",
        "query": {
            "feature_names": feature_names,
            "top_k": top_k
        },
        "summary": {
            "total_requested": len(feature_names),
            "found_count": len(results),
            "not_found_count": len(not_found),
            "not_found_features": not_found
        },
        "results": results
    }


def explain_variable_meaning(
    query: str,
    top_k: int = 3
) -> Dict[str, Any]:
    """
    工具二：解释变量含义和用法（支持中文名、featureN、自然语言）
    
    Args:
        query: 查询文本（如"灯丝电源电流"、"feature6"、"灯丝电源是什么"）
        top_k: 返回结果数量上限
    
    Returns:
        统一结构化结果
    """
    if not query or len(query.strip()) == 0:
        return {
            "success": False,
            "tool": "explain_variable_meaning",
            "message": "query 不能为空",
            "error": {
                "type": "invalid_input",
                "detail": "query 字符串为空",
                "suggestion": "请提供变量名或相关问题，如'灯丝电源电流'或'feature6'"
            }
        }
    
    querier = GenerationKGQuerier()
    if not querier.available:
        return {
            "success": False,
            "tool": "explain_variable_meaning",
            "message": "Generation 知识图谱不可用",
            "error": {
                "type": "kg_unavailable",
                "detail": "Neo4j 连接失败或 generation 数据库不存在",
                "suggestion": "请检查 Neo4j 服务状态和数据库配置"
            }
        }
    
    results = []
    
    # 策略 1：直接匹配 featureN
    query_lower = query.lower().strip()
    if query_lower.startswith("feature") and query_lower[7:].isdigit():
        var_name = FEATURE_MAPPING.get(query_lower)
        if var_name:
            node_info = querier.query_variable_by_name(var_name)
            if node_info:
                results.append({
                    "match_type": "exact_feature_id",
                    "feature_id": query_lower,
                    "variable_name": var_name,
                    "type": node_info.get("type"),
                    "parent_system": node_info.get("parent"),
                    "details": node_info.get("properties", {})
                })
    
    # 策略 2：直接匹配中文变量名
    if not results:
        if query in VARIABLE_TO_FEATURE:
            node_info = querier.query_variable_by_name(query)
            if node_info:
                results.append({
                    "match_type": "exact_variable_name",
                    "feature_id": VARIABLE_TO_FEATURE.get(query),
                    "variable_name": query,
                    "type": node_info.get("type"),
                    "parent_system": node_info.get("parent"),
                    "details": node_info.get("properties", {})
                })
    
    # 策略 3：jieba 分词后模糊匹配
    if not results and JIEBA_AVAILABLE:
        keywords = list(jieba.cut(query))
        keywords = [kw.strip() for kw in keywords if len(kw.strip()) > 1][:5]
        
        if keywords:
            fuzzy_nodes = querier.fuzzy_search_variables(keywords, limit=top_k)
            for node in fuzzy_nodes:
                results.append({
                    "match_type": "fuzzy_keyword",
                    "feature_id": VARIABLE_TO_FEATURE.get(node["name"]),
                    "variable_name": node["name"],
                    "type": node.get("type"),
                    "parent_system": node.get("parent"),
                    "details": node.get("properties", {})
                })
    
    querier.close()
    
    if not results:
        return {
            "success": True,
            "tool": "explain_variable_meaning",
            "message": f"未在 generation 知识图谱中找到与 '{query}' 相关的变量",
            "query": {"query": query, "top_k": top_k},
            "summary": {"matched_count": 0},
            "results": []
        }
    
    return {
        "success": True,
        "tool": "explain_variable_meaning",
        "message": f"从 generation 知识图谱找到 {len(results)} 个相关变量",
        "query": {"query": query, "top_k": top_k},
        "summary": {"matched_count": len(results)},
        "results": results[:top_k]
    }


def search_domain_knowledge(
    query: str,
    top_k: int = 5,
    doc_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    工具三：常规领域问答（束流/加速器/微电子，走常规 RAG）
    
    Args:
        query: 查询文本
        top_k: 返回结果数量
        doc_type: 文档类型过滤（预留，当前未实现）
    
    Returns:
        统一结构化结果
    """
    if not query or len(query.strip()) == 0:
        return {
            "success": False,
            "tool": "search_domain_knowledge",
            "message": "query 不能为空",
            "error": {
                "type": "invalid_input",
                "detail": "query 字符串为空",
                "suggestion": "请提供查询问题，如'束流强度如何测量'"
            }
        }
    
    # 尝试使用 HybridRetriever 检索
    try:
        from knowledge.retrievers.hybrid_retriever import HybridRetriever
        
        # 使用 parent_child_api 索引（可配置）
        index_path = "knowledge/vector_store/index/parent_child_api"
        if not os.path.exists(index_path):
            index_path = "knowledge/vector_store/index/parent_child_simple"
        
        if not os.path.exists(index_path):
            return {
                "success": False,
                "tool": "search_domain_knowledge",
                "message": "向量索引不存在",
                "error": {
                    "type": "index_not_found",
                    "detail": f"未找到可用索引目录",
                    "suggestion": "请先构建向量索引或检查索引路径配置"
                }
            }
        
        retriever = HybridRetriever(
            index_path=index_path,
            embedder_type="api"
        )
        
        raw_results = retriever.retrieve(query, top_k=top_k)
        
        results = [
            {
                "content": doc,
                "score": float(score),
                "source": "hybrid_retriever"
            }
            for doc, score in raw_results
        ]
        
        return {
            "success": True,
            "tool": "search_domain_knowledge",
            "message": f"从知识库检索到 {len(results)} 条相关知识",
            "query": {
                "query": query,
                "top_k": top_k,
                "doc_type": doc_type
            },
            "summary": {
                "retrieved_count": len(results),
                "index_path": index_path
            },
            "results": results
        }
        
    except Exception as e:
        return {
            "success": False,
            "tool": "search_domain_knowledge",
            "message": f"常规 RAG 检索失败",
            "error": {
                "type": "retriever_error",
                "detail": str(e),
                "suggestion": "请检查检索器配置和索引文件完整性"
            }
        }


# =========================
# 工具定义（OpenAI Function Calling 格式）
# =========================

RAG_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "explain_diagnosis_features",
            "description": (
                "承接异常诊断工具的输出结果，解释诊断出的异常特征（feature1-feature34）的物理含义、"
                "所属子系统、详细参数等。**严格从 generation 知识图谱查询，不回退到常规 RAG**。"
                "适用场景：diagnose_by_* 工具返回 top_features 后，需要深入理解这些特征的技术背景。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "feature_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "异常特征名列表，格式为 feature1-feature34，如 ['feature4', 'feature5', 'feature6']"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "可选。每个特征返回的相关知识条数，默认 3（当前返回节点完整详情）",
                        "default": 3
                    }
                },
                "required": ["feature_names"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "explain_variable_meaning",
            "description": (
                "解释单个变量的含义和用法，支持中文变量名（如'灯丝电源电流'）、featureN（如'feature6'）、"
                "或自然语言问题（如'灯丝电源是什么'）。**严格从 generation 知识图谱查询，不回退到常规 RAG**。"
                "适用场景：用户直接询问某个变量、传感器、子系统的含义和技术细节。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "查询文本，可以是变量名（'加速电源电压'）、featureN（'feature3'）或问题（'加速电源电压是什么'）"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "可选。返回结果数量上限，默认 3",
                        "default": 3
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_domain_knowledge",
            "description": (
                "从常规知识库检索束流、加速器、微电子设备相关的专业知识，使用混合检索（TF-IDF + 向量语义）。"
                "适用场景：回答领域概念、原理、技术细节等通用问题，如'束流强度如何测量'、'加速器的工作原理'、'离子注入工艺流程'。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "查询问题，如'束流强度的测量方法'、'加速器真空系统的作用'"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "可选。返回结果数量，默认 5",
                        "default": 5
                    },
                    "doc_type": {
                        "type": "string",
                        "description": "可选。文档类型过滤（预留参数）"
                    }
                },
                "required": ["query"]
            }
        }
    }
]

RAG_TOOL_FUNCTIONS = {
    "explain_diagnosis_features": explain_diagnosis_features,
    "explain_variable_meaning": explain_variable_meaning,
    "search_domain_knowledge": search_domain_knowledge
}
