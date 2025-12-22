"""FAISS向量存储"""
import numpy as np
import pickle
import os
from typing import List, Tuple, Optional


class FaissVectorStore:
    """FAISS向量存储和检索"""
    
    def __init__(self, dimension: Optional[int] = None):
        """
        初始化FAISS向量存储
        
        Args:
            dimension: 向量维度，如果要创建新索引则必需
        """
        self.dimension = dimension
        self.index = None
        self.documents = []
        
        if dimension is not None:
            self._create_index(dimension)
    
    def _create_index(self, dimension: int):
        """创建FAISS索引"""
        try:
            import faiss
            self.faiss = faiss
        except ImportError:
            raise ImportError("需要安装 faiss: pip install faiss-cpu 或 faiss-gpu")
        
        # 使用 IndexFlatL2 进行精确搜索
        self.index = self.faiss.IndexFlatL2(dimension)
        print(f"创建FAISS索引，维度: {dimension}")
    
    def add_documents(self, embeddings: np.ndarray, documents: List[str]):
        """
        添加文档和对应的向量到索引
        
        Args:
            embeddings: 文档向量，shape (n, dimension)
            documents: 文档文本列表
        """
        if self.index is None:
            self._create_index(embeddings.shape[1])
        
        if embeddings.shape[0] != len(documents):
            raise ValueError("向量数量和文档数量不匹配")
        
        # 确保是float32类型
        embeddings = embeddings.astype('float32')
        
        # 添加到索引
        self.index.add(embeddings)
        self.documents.extend(documents)
        
        print(f"添加 {len(documents)} 个文档到索引，当前总数: {len(self.documents)}")
    
    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        搜索最相似的文档
        
        Args:
            query_embedding: 查询向量，shape (1, dimension) 或 (dimension,)
            top_k: 返回结果数量
            
        Returns:
            (文档, 距离分数) 的列表，按相似度排序
        """
        if self.index is None or len(self.documents) == 0:
            return []
        
        # 确保查询向量是2D的
        if len(query_embedding.shape) == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        # 确保是float32类型
        query_embedding = query_embedding.astype('float32')
        
        # 搜索
        top_k = min(top_k, len(self.documents))
        distances, indices = self.index.search(query_embedding, top_k)
        
        # 构建结果
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.documents):
                # 将L2距离转换为相似度分数（距离越小，相似度越高）
                similarity = 1.0 / (1.0 + float(dist))
                results.append((self.documents[idx], similarity))
        
        return results
    
    def save(self, index_path: str, documents_path: str):
        """
        保存索引和文档
        
        Args:
            index_path: 索引文件路径
            documents_path: 文档文件路径
        """
        if self.index is None:
            raise ValueError("没有索引可以保存")
        
        # 保存FAISS索引
        os.makedirs(os.path.dirname(index_path) or '.', exist_ok=True)
        self.faiss.write_index(self.index, index_path)
        
        # 保存文档
        os.makedirs(os.path.dirname(documents_path) or '.', exist_ok=True)
        with open(documents_path, 'wb') as f:
            pickle.dump(self.documents, f)
        
        print(f"索引已保存到: {index_path}")
        print(f"文档已保存到: {documents_path}")
    
    def load(self, index_path: str, documents_path: str):
        """
        加载索引和文档
        
        Args:
            index_path: 索引文件路径
            documents_path: 文档文件路径
        """
        try:
            import faiss
            self.faiss = faiss
        except ImportError:
            raise ImportError("需要安装 faiss: pip install faiss-cpu 或 faiss-gpu")
        
        # 加载FAISS索引
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"索引文件不存在: {index_path}")
        
        self.index = self.faiss.read_index(index_path)
        self.dimension = self.index.d
        
        # 加载文档
        if not os.path.exists(documents_path):
            raise FileNotFoundError(f"文档文件不存在: {documents_path}")
        
        with open(documents_path, 'rb') as f:
            self.documents = pickle.load(f)
        
        print(f"加载索引: {len(self.documents)} 个文档，维度: {self.dimension}")
    
    def get_stats(self) -> dict:
        """
        获取存储统计信息
        
        Returns:
            统计信息字典
        """
        return {
            "total_documents": len(self.documents),
            "dimension": self.dimension,
            "index_size": self.index.ntotal if self.index else 0
        }

