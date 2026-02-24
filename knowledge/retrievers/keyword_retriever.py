"""
关键词检索器 - 基于 TF-IDF + jieba 中文分词
针对中文文本和短文档进行了优化
"""
import jieba
from typing import List, Tuple, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os

from .base_retriever import BaseRetriever


class KeywordRetriever(BaseRetriever):
    """
    关键词检索器 - 基于 TF-IDF + jieba 中文分词
    
    特点：
    - 使用 jieba 进行中文分词，提高关键词匹配准确率
    - 精确关键词匹配
    - 速度快，无需深度学习模型
    - 适合专业术语检索
    - 对短文本友好（使用对数尺度词频）
    """
    
    def __init__(
        self, 
        index_path: str,
        max_features: int = 10000,
        ngram_range: tuple = (1, 2),
        min_df: int = 1,
        use_idf: bool = True,
        sublinear_tf: bool = True
    ):
        """
        初始化关键词检索器（从索引加载）
        
        Args:
            index_path: 索引目录路径（包含 embedder.pkl 的目录）
            max_features: 最大特征数（仅在从索引加载时用于显示）
            ngram_range: n-gram 范围（仅在从索引加载时用于显示）
            min_df: 最小文档频率（仅在从索引加载时用于显示）
            use_idf: 是否使用 IDF（仅在从索引加载时用于显示）
            sublinear_tf: 是否使用对数尺度的词频（仅在从索引加载时用于显示）
        """
        # 检查索引路径
        if not os.path.exists(index_path):
            raise ValueError(f"索引路径不存在: {index_path}")
        
        print(f"[KeywordRetriever] 从索引加载: {index_path}")
        
        # 确定文件路径
        if os.path.isdir(index_path):
            index_dir = index_path
            embedder_file = os.path.join(index_dir, "embedder.pkl")
            documents_file = os.path.join(index_dir, "documents.pkl")
        else:
            raise ValueError(f"index_path 必须是目录: {index_path}")
        
        # 加载 TF-IDF embedder
        if not os.path.exists(embedder_file):
            raise FileNotFoundError(f"TF-IDF embedder 文件不存在: {embedder_file}")
        
        print(f"[KeywordRetriever] 加载 TF-IDF embedder...")
        with open(embedder_file, 'rb') as f:
            tfidf_data = pickle.load(f)
            self.vectorizer = tfidf_data['vectorizer']
            self.tfidf_matrix = tfidf_data['tfidf_matrix']
        
        # 加载文档
        if not os.path.exists(documents_file):
            raise FileNotFoundError(f"文档文件不存在: {documents_file}")
        
        print(f"[KeywordRetriever] 加载文档...")
        with open(documents_file, 'rb') as f:
            self.documents = pickle.load(f)
        
        print(f"[KeywordRetriever] 索引加载完成")
        print(f"  - 文档数量: {len(self.documents)}")
        print(f"  - TF-IDF 矩阵 shape: {self.tfidf_matrix.shape}")
        print(f"  - 词汇表大小: {len(self.vectorizer.vocabulary_)}")
        
        # 加载元数据（如果存在）
        metadata_file = os.path.join(index_dir, "metadata.pkl")
        self.metadata_list = []
        if os.path.exists(metadata_file):
            with open(metadata_file, 'rb') as f:
                self.metadata_list = pickle.load(f)
            print(f"[KeywordRetriever] 元数据加载完成: {len(self.metadata_list)} 条记录")
    
    def _segment(self, text: str) -> str:
        """
        使用 jieba 对文本进行分词
        
        Args:
            text: 原始文本
            
        Returns:
            分词后的文本（空格分隔）
        """
        # 使用 jieba 分词
        words = jieba.cut(text)
        # 过滤停用词和标点（可选）
        words = [w.strip() for w in words if len(w.strip()) > 0]
        return ' '.join(words)
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        基于 TF-IDF 检索最相关的文档。
        若索引含 parent_chunk 元数据，则返回父块（同一父块去重，保留最高分）。
        
        Args:
            query: 查询文本
            top_k: 返回前 k 个结果
            
        Returns:
            (文档内容, 相似度分数) 的列表，文档为父块（若有）或子块
        """
        segmented_query = self._segment(query)
        query_vec = self.vectorizer.transform([segmented_query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix)[0]
        
        # 若有 parent_chunk，多取一些以便去重后仍有足够父块
        fetch_k = top_k * 3 if getattr(self, 'metadata_list', None) else top_k
        top_indices = np.argsort(similarities)[::-1][:fetch_k]
        
        results = [
            (self.documents[idx], float(similarities[idx]))
            for idx in top_indices
        ]
        
        return self._apply_parent_chunks(results, top_k)
    
    def get_statistics(self) -> dict:
        """
        获取检索器统计信息
        
        Returns:
            统计信息字典
        """
        return {
            'retriever_type': 'KeywordRetriever',
            'num_documents': len(self.documents),
            'tfidf_shape': self.tfidf_matrix.shape,
            'vocab_size': len(self.vectorizer.vocabulary_),
            'avg_doc_length': np.mean([len(doc) for doc in self.documents])
        }
