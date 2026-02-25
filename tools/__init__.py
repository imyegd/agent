from .data_query import (
    DataQueryTool, 
    query_beam_data, 
    get_data_info,
    DATA_QUERY_TOOLS,
    DATA_QUERY_TOOL_FUNCTIONS
)
from .anomaly_detection import (
    AnomalyDetectionTool,
    detect_anomaly,
    ANOMALY_DETECTION_TOOLS,
    ANOMALY_DETECTION_TOOL_FUNCTIONS
)
from .anomaly_diagnose import (
    diagnose_by_statistical_difference,
    diagnose_by_pls,
    diagnose_by_shap,
    diagnose_by_autoencoder,
    ANOMALY_DIAGNOSIS_TOOLS,
    ANOMALY_DIAGNOSIS_TOOL_FUNCTIONS
)
# 尝试导入 RAG 工具（可选）
try:
    from knowledge.rag_tool import (
        RAG_TOOLS,
        RAG_TOOL_FUNCTIONS,
        explain_diagnosis_features,
        explain_variable_meaning,
        search_domain_knowledge
    )
    RAG_AVAILABLE = True
except ImportError as e:
    RAG_AVAILABLE = False
    RAG_TOOLS = []
    RAG_TOOL_FUNCTIONS = {}
    print(f"警告: RAG 知识库模块不可用，相关功能将被禁用 ({e})")

# 汇总所有工具
TOOLS = (
    DATA_QUERY_TOOLS + 
    ANOMALY_DETECTION_TOOLS + 
    ANOMALY_DIAGNOSIS_TOOLS + 
    RAG_TOOLS
)

# 汇总所有工具函数映射
TOOL_FUNCTIONS = {}
TOOL_FUNCTIONS.update(DATA_QUERY_TOOL_FUNCTIONS)
TOOL_FUNCTIONS.update(ANOMALY_DETECTION_TOOL_FUNCTIONS)
TOOL_FUNCTIONS.update(ANOMALY_DIAGNOSIS_TOOL_FUNCTIONS)
TOOL_FUNCTIONS.update(RAG_TOOL_FUNCTIONS)

__all__ = [
    # 数据查询
    'DataQueryTool', 'query_beam_data', 'get_data_info',
    # 异常检测
    'AnomalyDetectionTool', 'detect_anomaly',
    # 异常诊断
    'diagnose_by_statistical_difference', 'diagnose_by_pls', 
    'diagnose_by_shap', 'diagnose_by_autoencoder',
    # RAG 工具
    'explain_diagnosis_features', 'explain_variable_meaning', 'search_domain_knowledge',
    # 工具汇总
    'TOOLS', 'TOOL_FUNCTIONS'
]

