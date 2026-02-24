"""
混合检索器 - 结合向量检索和 TF-IDF 检索，使用 RRF 融合
"""
from typing import List, Tuple, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import jieba
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


class HybridRetriever(BaseRetriever):
    """
    混合检索器 - 结合向量检索和 TF-IDF 检索，使用 RRF 融合
    
    原理:
    1. 向量检索: 使用 embedding 向量的语义相似度
    2. TF-IDF 检索: 基于关键词的传统文本匹配
    3. RRF 融合: Reciprocal Rank Fusion，综合两种排名
    
    RRF 公式: Score(d) = Σ 1/(k + rank(d,r))
    
    特点：
    - 综合关键词和语义检索的优势
    - 对不同类型的查询都有较好的鲁棒性
    - 适合生产环境
    """
    
    def __init__(
        self,
        index_path: str,
        embedder_type: str = "api",
        rrf_k: int = 60,
        max_features: int = 5000,
        ngram_range: Tuple[int, int] = (1, 2),
        **embedder_kwargs
    ):
        """
        初始化混合检索器
        
        Args:
            index_path: FAISS 索引路径
            embedder_type: 向量化方法 ("api", "local", "simple")
            rrf_k: RRF 平滑常数，通常 60
            max_features: TF-IDF 最大特征数
            ngram_range: N-gram 范围
            **embedder_kwargs: 传递给 embedder 的参数
        """
        self.embedder_type = embedder_type
        self.rrf_k = rrf_k
        self.vector_store = None
        self.metadata_list = []
        
        # 1. 加载 FAISS 索引
        if not os.path.exists(index_path):
            raise ValueError(f"索引路径不存在: {index_path}")
        
        print(f"[HybridRetriever] 加载向量索引: {index_path}")
        
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
        
        # 创建 embedder
        self.embedder = create_embedder(embedder_type, **embedder_kwargs)
        
        # 创建向量存储实例并加载
        self.vector_store = FaissVectorStore()
        self.vector_store.load(index_file, documents_file)
        self.documents = self.vector_store.documents
        print(f"[HybridRetriever] 索引加载完成: {len(self.documents)} 个文档")
        
        # 加载元数据（如果存在）
        metadata_file = os.path.join(index_dir, "metadata.pkl")
        if os.path.exists(metadata_file):
            import pickle
            with open(metadata_file, 'rb') as f:
                self.metadata_list = pickle.load(f)
            print(f"[HybridRetriever] 元数据加载完成: {len(self.metadata_list)} 条记录")
        
        # 2. 初始化 TF-IDF 检索器（使用 jieba 分词）
        print(f"[HybridRetriever] 构建 TF-IDF 索引（使用 jieba 分词）...")
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=ngram_range,
            min_df=1,
            analyzer='word',  # 使用词级别分析
            token_pattern=r"(?u)\b\w+\b"  # 匹配中文字符
        )
        # 对文档进行分词
        segmented_docs = [self._segment(doc) for doc in self.documents]
        self.tfidf_matrix = self.vectorizer.fit_transform(segmented_docs)
        print(f"[HybridRetriever] TF-IDF 索引完成，shape: {self.tfidf_matrix.shape}")
    
    def _segment(self, text: str) -> str:
        """
        使用 jieba 对文本进行分词
        
        Args:
            text: 原始文本
            
        Returns:
            分词后的文本（空格分隔）
        """
        words = jieba.cut(text)
        words = [w.strip() for w in words if len(w.strip()) > 0]
        return ' '.join(words)
    
    def _vector_search(self, query: str, top_k: int) -> List[Tuple[int, float]]:
        """向量检索，返回 [(doc_idx, score), ...]"""
        query_embedding = self.embedder.embed([query])[0]
        
        # 使用 vector_store 的 search 方法
        results = self.vector_store.search(query_embedding, top_k)
        
        # 将文档转换为索引
        doc_to_idx = {doc: idx for idx, doc in enumerate(self.documents)}
        indexed_results = []
        for doc, score in results:
            if doc in doc_to_idx:
                indexed_results.append((doc_to_idx[doc], score))
        
        return indexed_results
    
    def _tfidf_search(self, query: str, top_k: int) -> List[Tuple[int, float]]:
        """TF-IDF 检索，返回 [(doc_idx, score), ...]"""
        # 对查询进行分词
        segmented_query = self._segment(query)
        query_vec = self.vectorizer.transform([segmented_query])
        
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        return [(int(idx), float(similarities[idx])) for idx in top_indices]
    
    def _rrf_fusion(
        self,
        vector_results: List[Tuple[int, float]],
        tfidf_results: List[Tuple[int, float]],
        top_k: int
    ) -> List[Tuple[int, float]]:
        """
        RRF (Reciprocal Rank Fusion) 融合两个排名列表
        
        公式: Score(d) = Σ 1/(k + rank(d,r))
        """
        # 构建排名字典
        vector_ranks = {doc_idx: rank + 1 for rank, (doc_idx, _) in enumerate(vector_results)}
        tfidf_ranks = {doc_idx: rank + 1 for rank, (doc_idx, _) in enumerate(tfidf_results)}
        
        # 获取所有出现过的文档
        all_doc_ids = set(vector_ranks.keys()) | set(tfidf_ranks.keys())
        
        # 计算 RRF 分数
        rrf_scores = {}
        for doc_idx in all_doc_ids:
            score = 0.0
            
            if doc_idx in vector_ranks:
                score += 1.0 / (self.rrf_k + vector_ranks[doc_idx])
            
            if doc_idx in tfidf_ranks:
                score += 1.0 / (self.rrf_k + tfidf_ranks[doc_idx])
            
            rrf_scores[doc_idx] = score
        
        # 按 RRF 分数排序
        sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        return sorted_docs
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        使用混合检索（向量 + TF-IDF + RRF 融合）
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            
        Returns:
            [(document, score), ...]
        """
        # 若有 parent_chunk，多取候选以便去重后仍有足够父块
        fetch_k = top_k * 3 if getattr(self, 'metadata_list', None) else top_k * 2
        
        # 1. 向量检索
        vector_results = self._vector_search(query, fetch_k)
        
        # 2. TF-IDF 检索
        tfidf_results = self._tfidf_search(query, fetch_k)
        
        # 3. RRF 融合
        fused_results = self._rrf_fusion(vector_results, tfidf_results, top_k * 2)
        
        # 4. 构建结果（子块），再转为父块（若有 parent_chunk）并去重
        raw_results = []
        for doc_idx, score in fused_results:
            if doc_idx < len(self.documents):
                raw_results.append((self.documents[doc_idx], score))
        
        return self._apply_parent_chunks(raw_results, top_k)
    
    def get_statistics(self) -> dict:
        """获取统计信息"""
        return {
            'retriever_type': 'HybridRetriever',
            'embedder_type': self.embedder_type,
            'document_count': len(self.documents),
            'rrf_k': self.rrf_k,
            'embedding_dimension': self.vector_store.dimension if self.vector_store else 0,
            'vocabulary_size': len(self.vectorizer.vocabulary_),
            'tfidf_matrix_shape': self.tfidf_matrix.shape,
            'using_faiss_index': self.vector_store is not None
        }
