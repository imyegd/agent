"""
知识库模块 - RAG系统
"""

# 新版离线/在线架构
from .offline_processor import OfflineProcessor
from .online_retriever import OnlineRetriever, create_retriever

# RAG工具（供LLM调用）
from .rag_tool import (
    RAGTool,
    search_knowledge,
    explain_features,
    get_troubleshooting_solutions,
    RAG_TOOLS,
    RAG_TOOL_FUNCTIONS
)

# 旧版接口（向后兼容）
from .knowledge_base import KnowledgeBase
from .embeddings import BaseEmbedder, SimpleEmbedder, APIEmbedder, HybridEmbedder, create_embedder
from .retriever import KnowledgeRetriever

__all__ = [
    # 新版核心
    'OfflineProcessor',
    'OnlineRetriever',
    'create_retriever',
    'RAGTool',
    
    # 工具函数（供LLM调用）
    'search_knowledge',
    'explain_features',
    'get_troubleshooting_solutions',
    'RAG_TOOLS',
    'RAG_TOOL_FUNCTIONS',
    
    # 旧版核心类（兼容）
    'KnowledgeBase',
    'KnowledgeRetriever',
    
    # Embedder相关
    'BaseEmbedder',
    'SimpleEmbedder',
    'APIEmbedder',
    'HybridEmbedder',
    'create_embedder'
]

