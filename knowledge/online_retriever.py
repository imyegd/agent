"""在线检索服务 - 基于离线构建的FAISS索引"""
import os
import pickle
from typing import List, Dict, Any, Optional
from .vector_store import FaissVectorStore
from .embeddings import create_embedder


class OnlineRetriever:
    """在线检索器 - 加载离线索引并提供检索服务"""
    
    def __init__(
        self,
        index_path: str = "knowledge/vector_store/faiss_index.bin",
        docs_path: str = "knowledge/vector_store/documents.pkl",
        metadata_path: str = "knowledge/vector_store/metadata.pkl",
        embedder_type: str = "simple",
        **embedder_kwargs
    ):
        """
        初始化在线检索器
        
        Args:
            index_path: FAISS索引文件路径
            docs_path: 文档文件路径
            metadata_path: 元数据文件路径
            embedder_type: 向量化方法（需与离线处理一致）
            **embedder_kwargs: embedder参数
        """
        self.index_path = index_path
        self.docs_path = docs_path
        self.metadata_path = metadata_path
        
        # 初始化embedder
        self.embedder = create_embedder(embedder_type, **embedder_kwargs)
        
        # 加载向量存储
        self.vector_store = FaissVectorStore()
        self.metadata = []
        
        self._load_index()
    
    def _load_index(self):
        """加载离线构建的索引"""
        print("加载知识库索引...")
        
        # 检查文件是否存在
        if not os.path.exists(self.index_path):
            raise FileNotFoundError(f"索引文件不存在: {self.index_path}")
        
        if not os.path.exists(self.docs_path):
            raise FileNotFoundError(f"文档文件不存在: {self.docs_path}")
        
        # 加载FAISS索引和文档
        self.vector_store.load(self.index_path, self.docs_path)
        
        # 加载元数据
        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, 'rb') as f:
                self.metadata = pickle.load(f)
            print(f"加载元数据: {len(self.metadata)} 条")
        
        # 训练embedder（如果是SimpleEmbedder）
        if hasattr(self.embedder, 'fit'):
            if not self.embedder.fitted:
                print("训练向量化器...")
                self.embedder.fit(self.vector_store.documents)
        
        print(f"索引加载完成: {len(self.vector_store.documents)} 个文档块")
    
    def search(
        self, 
        query: str, 
        top_k: int = 5,
        return_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        检索相关知识
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            return_metadata: 是否返回元数据
            
        Returns:
            检索结果列表，每个结果包含document, score, metadata
        """
        if not query or not query.strip():
            return []
        
        # 向量化查询
        query_embedding = self.embedder.embed(query)
        
        # 检索
        raw_results = self.vector_store.search(query_embedding, top_k=top_k)
        
        # 构建结果
        results = []
        for doc, score in raw_results:
            result = {
                "document": doc,
                "score": score
            }
            
            # 添加元数据
            if return_metadata and self.metadata:
                # 找到对应的元数据
                doc_idx = self.vector_store.documents.index(doc)
                if doc_idx < len(self.metadata):
                    result["metadata"] = self.metadata[doc_idx]
            
            results.append(result)
        
        return results
    
    def search_by_source(
        self,
        query: str,
        source_file: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        在指定来源文件中检索
        
        Args:
            query: 查询文本
            source_file: 来源文件名
            top_k: 返回结果数量
            
        Returns:
            检索结果列表
        """
        # 先检索大量结果
        all_results = self.search(query, top_k=top_k * 5, return_metadata=True)
        
        # 过滤指定来源
        filtered = [
            r for r in all_results 
            if r.get("metadata", {}).get("source_file") == source_file
        ]
        
        return filtered[:top_k]
    
    def get_random_samples(self, n: int = 5) -> List[str]:
        """
        获取随机样本文档
        
        Args:
            n: 样本数量
            
        Returns:
            文档列表
        """
        import random
        if len(self.vector_store.documents) < n:
            return self.vector_store.documents
        
        return random.sample(self.vector_store.documents, n)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取检索器统计信息
        
        Returns:
            统计信息字典
        """
        stats = self.vector_store.get_stats()
        
        # 添加来源文件统计
        if self.metadata:
            source_files = set(m.get("source_file") for m in self.metadata)
            stats["source_files"] = list(source_files)
            stats["source_file_count"] = len(source_files)
        
        return stats


def create_retriever(
    embedder_type: str = "simple",
    **kwargs
) -> OnlineRetriever:
    """
    创建在线检索器的工厂函数
    
    Args:
        embedder_type: 向量化方法
        **kwargs: 传递给OnlineRetriever的参数
        
    Returns:
        OnlineRetriever实例
    """
    return OnlineRetriever(embedder_type=embedder_type, **kwargs)

