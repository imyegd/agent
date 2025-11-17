from .data_query import (
    DataQueryTool, 
    query_beam_data, 
    get_data_info,
    DATA_QUERY_TOOLS,
    DATA_QUERY_TOOL_FUNCTIONS
)
from .pls_analysis import (
    PLSAnalysisTool, 
    analyze_beam_fluctuation,
    PLS_ANALYSIS_TOOLS,
    PLS_ANALYSIS_TOOL_FUNCTIONS
)
from .beam_visualization import (
    BeamVisualizationTool, 
    visualize_beam_fluctuation,
    VISUALIZATION_TOOLS,
    VISUALIZATION_TOOL_FUNCTIONS
)

# 尝试导入 RAG 工具（可选）
try:
    from knowledge import (
        RAG_TOOLS,
        RAG_TOOL_FUNCTIONS,
        search_knowledge,
        explain_features,
        get_troubleshooting_solutions
    )
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    RAG_TOOLS = []
    RAG_TOOL_FUNCTIONS = {}
    print("警告: RAG 知识库模块不可用，相关功能将被禁用")

# 汇总所有工具
TOOLS = DATA_QUERY_TOOLS + PLS_ANALYSIS_TOOLS + VISUALIZATION_TOOLS + RAG_TOOLS

# 汇总所有工具函数映射
TOOL_FUNCTIONS = {}
TOOL_FUNCTIONS.update(DATA_QUERY_TOOL_FUNCTIONS)
TOOL_FUNCTIONS.update(PLS_ANALYSIS_TOOL_FUNCTIONS)
TOOL_FUNCTIONS.update(VISUALIZATION_TOOL_FUNCTIONS)
TOOL_FUNCTIONS.update(RAG_TOOL_FUNCTIONS)

__all__ = [
    'DataQueryTool', 'query_beam_data', 'get_data_info', 
    'PLSAnalysisTool', 'analyze_beam_fluctuation',
    'BeamVisualizationTool', 'visualize_beam_fluctuation',
    'TOOLS', 'TOOL_FUNCTIONS'
]

