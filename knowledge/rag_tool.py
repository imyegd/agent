"""
RAG 工具封装 - 供 LLM 调用
"""
from typing import Dict, Any, List, Optional
from .knowledge_base import KnowledgeBase
from .retriever import KnowledgeRetriever


# 全局单例，避免重复加载
_global_retriever = None


def get_retriever() -> KnowledgeRetriever:
    """获取全局检索器实例（单例模式）"""
    global _global_retriever
    if _global_retriever is None:
        _global_retriever = KnowledgeRetriever()
    return _global_retriever


class RAGTool:
    """RAG 工具类"""
    
    def __init__(self):
        """初始化 RAG 工具"""
        self.retriever = get_retriever()
        self.kb = self.retriever.kb
    
    def search_knowledge(
        self, 
        query: str, 
        top_k: int = 3,
        doc_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        搜索知识库
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            doc_type: 文档类型过滤，可选 "feature", "solution", "concept"
            
        Returns:
            搜索结果字典
        """
        try:
            results = self.retriever.search(query, top_k, doc_type)
            
            return {
                "success": True,
                "query": query,
                "results_count": len(results),
                "results": [
                    {
                        "content": r["document"],
                        "score": r["score"],
                        "type": r["metadata"].get("type"),
                        "metadata": r["metadata"]
                    }
                    for r in results
                ]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"知识检索失败: {str(e)}"
            }
    
    def explain_features(
        self, 
        feature_names: List[str],
        include_solutions: bool = False
    ) -> Dict[str, Any]:
        """
        解释特征的物理含义
        
        Args:
            feature_names: 特征名称列表
            include_solutions: 是否包含相关解决方案
            
        Returns:
            特征解释字典
        """
        try:
            explanations = self.retriever.get_feature_explanations(feature_names)
            
            result = {
                "success": True,
                "feature_count": len(feature_names),
                "features": {}
            }
            
            # 格式化特征信息
            for feat_name in feature_names:
                if feat_name in explanations:
                    feat_info = explanations[feat_name]
                    result["features"][feat_name] = {
                        "name": feat_info.get("name", "未知"),
                        "description": feat_info.get("description", ""),
                        "unit": feat_info.get("unit", ""),
                        "normal_range": feat_info.get("normal_range", ""),
                        "related_to": feat_info.get("related_to", ""),
                        "anomaly_causes": feat_info.get("anomaly_causes", []),
                        "impact": feat_info.get("impact", "")
                    }
                else:
                    result["features"][feat_name] = {
                        "name": feat_name,
                        "description": "该特征的物理含义暂未录入知识库"
                    }
            
            # 如果需要，查找相关解决方案
            if include_solutions:
                problem_desc = f"{', '.join(feature_names)} 异常"
                solutions = self.retriever.find_solutions(problem_desc, feature_names, top_k=2)
                result["related_solutions"] = [
                    {
                        "problem": s.get("problem"),
                        "solutions": s.get("solutions", [])[:3],  # 只返回前3个解决方案
                        "priority": s.get("priority")
                    }
                    for s in solutions
                ]
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"特征解释失败: {str(e)}"
            }
    
    def get_solutions(
        self, 
        problem_description: str,
        feature_names: Optional[List[str]] = None,
        top_k: int = 3
    ) -> Dict[str, Any]:
        """
        获取解决方案建议
        
        Args:
            problem_description: 问题描述
            feature_names: 相关特征名称列表
            top_k: 返回结果数量
            
        Returns:
            解决方案字典
        """
        try:
            solutions = self.retriever.find_solutions(
                problem_description, 
                feature_names, 
                top_k
            )
            
            return {
                "success": True,
                "query": problem_description,
                "solutions_count": len(solutions),
                "solutions": [
                    {
                        "problem": s.get("problem"),
                        "symptoms": s.get("symptoms", []),
                        "root_causes": s.get("root_causes", []),
                        "solutions": s.get("solutions", []),
                        "priority": s.get("priority"),
                        "typical_resolution_time": s.get("typical_resolution_time"),
                        "relevance_score": s.get("relevance_score", 0)
                    }
                    for s in solutions
                ]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"解决方案查询失败: {str(e)}"
            }
    
    def get_comprehensive_analysis(
        self, 
        anomaly_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        获取综合分析和建议（用于PLS分析结果增强）
        
        Args:
            anomaly_info: 异常信息字典，应包含 T2X_top_features, SPEX_top_features 等
            
        Returns:
            综合分析结果
        """
        try:
            recommendations = self.retriever.get_recommendations(anomaly_info)
            
            return {
                "success": True,
                "has_recommendations": len(recommendations.get("solutions", [])) > 0,
                "summary": recommendations.get("summary", ""),
                "feature_explanations": recommendations.get("feature_explanations", {}),
                "solutions": recommendations.get("solutions", [])[:3],  # 最多3个解决方案
                "relevant_concepts": recommendations.get("relevant_concepts", [])[:2]  # 最多2个概念
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"综合分析失败: {str(e)}"
            }


# ========== 供 LLM 调用的工具函数 ==========

def search_knowledge(
    query: str, 
    top_k: int = 3,
    doc_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    搜索束流数据分析相关的知识库
    
    Args:
        query: 搜索查询，例如 "电压传感器异常原因"
        top_k: 返回结果数量，默认3
        doc_type: 文档类型，可选 "feature"(特征), "solution"(解决方案), "concept"(概念)
    
    Returns:
        包含搜索结果的字典
    """
    tool = RAGTool()
    return tool.search_knowledge(query, top_k, doc_type)


def explain_features(
    feature_names: List[str],
    include_solutions: bool = False
) -> Dict[str, Any]:
    """
    获取特征的物理含义和详细解释
    
    Args:
        feature_names: 特征名称列表，如 ['feature1', 'feature2']
        include_solutions: 是否包含相关解决方案建议
    
    Returns:
        包含特征解释的字典
    """
    tool = RAGTool()
    return tool.explain_features(feature_names, include_solutions)


def get_troubleshooting_solutions(
    problem_description: str,
    feature_names: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    获取故障排查和解决方案建议
    
    Args:
        problem_description: 问题描述，如 "束流强度不稳定"
        feature_names: 相关异常特征列表（可选）
    
    Returns:
        包含解决方案的字典
    """
    tool = RAGTool()
    return tool.get_solutions(problem_description, feature_names, top_k=3)


# ========== 工具定义（OpenAI Function Calling 格式）==========

RAG_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": "搜索束流数据分析相关的知识库，获取专业解释、概念定义和技术细节。适合回答'什么是XXX'、'XXX的原理'等问题。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询，例如 '电压传感器异常原因'、'T2统计量的含义'"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "返回结果数量，默认3",
                        "default": 3
                    },
                    "doc_type": {
                        "type": "string",
                        "enum": ["feature", "solution", "concept"],
                        "description": "文档类型过滤：feature(特征), solution(解决方案), concept(概念)"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "explain_features",
            "description": "获取特征（传感器变量）的物理含义、正常范围、可能的异常原因等详细信息。当需要解释feature1-feature35的含义时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "feature_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "特征名称列表，如 ['feature1', 'feature3', 'feature12']"
                    },
                    "include_solutions": {
                        "type": "boolean",
                        "description": "是否包含相关解决方案建议，默认false",
                        "default": False
                    }
                },
                "required": ["feature_names"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_troubleshooting_solutions",
            "description": "根据问题描述和异常特征，获取故障排查步骤和解决方案建议。适合回答'如何解决XXX问题'、'XXX异常的处理方法'。",
            "parameters": {
                "type": "object",
                "properties": {
                    "problem_description": {
                        "type": "string",
                        "description": "问题描述，如 '束流强度不稳定'、'真空度异常'、'位置振荡增大'"
                    },
                    "feature_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "相关异常特征列表（可选），如 ['feature3', 'feature8']"
                    }
                },
                "required": ["problem_description"]
            }
        }
    }
]

# 工具函数映射
RAG_TOOL_FUNCTIONS = {
    "search_knowledge": search_knowledge,
    "explain_features": explain_features,
    "get_troubleshooting_solutions": get_troubleshooting_solutions
}

