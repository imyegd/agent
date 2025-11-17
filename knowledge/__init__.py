"""
知识库模块 - RAG系统
"""
from .knowledge_base import KnowledgeBase
from .embeddings import BaseEmbedder, SimpleEmbedder, APIEmbedder, HybridEmbedder, create_embedder
from .retriever import KnowledgeRetriever
from .rag_tool import (
    RAGTool,
    search_knowledge,
    explain_features,
    get_troubleshooting_solutions,
    RAG_TOOLS,
    RAG_TOOL_FUNCTIONS
)

__all__ = [
    # 核心类
    'KnowledgeBase',
    'KnowledgeRetriever',
    'RAGTool',
    
    # Embedder相关
    'BaseEmbedder',
    'SimpleEmbedder',
    'APIEmbedder',
    'HybridEmbedder',
    'create_embedder',
    
    # 工具函数（供LLM调用）
    'search_knowledge',
    'explain_features',
    'get_troubleshooting_solutions',
    
    # 工具定义
    'RAG_TOOLS',
    'RAG_TOOL_FUNCTIONS'
]

