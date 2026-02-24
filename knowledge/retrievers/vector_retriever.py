"""
向量检索器 - 基于语义相似度
"""
from typing import List, Tuple, Optional
import numpy as np
import sys
import os

# 处理导入路径
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from knowledge.embeddings import create_embedder
    from knowledge.retrievers.base_retriever import BaseRetriever
    from knowledge.vector_store.faiss_store import FaissVectorStore
else:
    from ..embeddings import create_embedder
    from .base_retriever import BaseRetriever
    from ..vector_store.faiss_store import FaissVectorStore


class VectorRetriever(BaseRetriever):
    """
    向量检索器 - 基于语义相似度
    
    特点：
    - 理解语义和上下文
    - 支持同义词和相似表达
    - 适合自然语言问答
    """
    
    def __init__(
        self,
        index_path: str,
        embedder_type: str = "api",
        **embedder_kwargs
    ):
        """
        初始化向量检索器
        
        Args:
            index_path: FAISS 索引路径
            embedder_type: 向量化方法 ("api", "local", "simple")
            **embedder_kwargs: 传递给 embedder 的参数
        """
        self.embedder_type = embedder_type
        self.vector_store = None
        self.metadata_list = []
        
        # 初始化 embedder
        self.embedder = create_embedder(embedder_type, **embedder_kwargs)
        
        # 加载 FAISS 索引
        if not os.path.exists(index_path):
            raise ValueError(f"索引路径不存在: {index_path}")
        
        print(f"[VectorRetriever] 加载向量索引: {index_path}")
        
        # 确定索引和文档文件路径
        if os.path.isdir(index_path):
            index_dir = index_path
            index_file = os.path.join(index_dir, "faiss_index.bin")
            documents_file = os.path.join(index_dir, "documents.pkl")
        else:
            # 如果传入的是文件，假设在同一目录下有对应的 documents.pkl
            index_file = index_path
            index_dir = os.path.dirname(index_path)
            documents_file = os.path.join(index_dir, "documents.pkl")
        
        # 创建向量存储实例并加载
        self.vector_store = FaissVectorStore()
        self.vector_store.load(index_file, documents_file)
        self.documents = self.vector_store.documents
        print(f"[VectorRetriever] 索引加载完成: {len(self.documents)} 个文档")
        
        # 加载元数据（如果存在）
        metadata_file = os.path.join(index_dir, "metadata.pkl")
        if os.path.exists(metadata_file):
            import pickle
            with open(metadata_file, 'rb') as f:
                self.metadata_list = pickle.load(f)
            print(f"[VectorRetriever] 元数据加载完成: {len(self.metadata_list)} 条记录")
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        使用向量相似度检索。
        若索引含 parent_chunk 元数据，则返回父块（同一父块去重，保留最高分）。
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            
        Returns:
            [(document, score), ...]，document 为父块（若有）或子块
        """
        query_embedding = self.embedder.embed([query])[0]
        
        # 若有 parent_chunk，多取一些子块以便去重后仍有足够父块
        fetch_k = top_k * 3 if getattr(self, 'metadata_list', None) else top_k
        results = self.vector_store.search(query_embedding, fetch_k)
        
        return self._apply_parent_chunks(results, top_k)
    
    def get_statistics(self) -> dict:
        """获取统计信息"""
        dimension = 0
        if self.vector_store is not None:
            dimension = self.vector_store.dimension
        
        return {
            'retriever_type': 'VectorRetriever',
            'embedder_type': self.embedder_type,
            'document_count': len(self.documents),
            'embedding_dimension': dimension,
            'using_faiss_index': self.vector_store is not None
        }
