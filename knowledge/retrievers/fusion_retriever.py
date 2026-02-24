"""
融合检索器
结合混合检索（TF-IDF + Vector）和知识图谱检索，统一重排
"""
import time
import numpy as np
from typing import List, Tuple
from sklearn.metrics.pairwise import cosine_similarity

from .hybrid_retriever import HybridRetriever
from .kg_retriever import KGRetriever
from knowledge.embeddings import create_embedder
from config.config import Config

# 默认：遇 429 时重试次数、初始退避秒数、批间延迟秒数
DEFAULT_RERANK_MAX_RETRIES = 3
DEFAULT_RERANK_BACKOFF_SEC = 2.0
DEFAULT_RERANK_BATCH_DELAY_SEC = 1.0


class FusionRetriever:
    """
    融合检索器
    
    工作流程：
    1. 混合检索（TF-IDF + Vector + RRF）
    2. KG 检索（jieba 分词 + 节点匹配 + 邻居）
    3. 合并去重
    4. Embedding 相似度统一重排
    5. 返回最终 top_k
    """
    
    def __init__(
        self,
        index_path: str,
        embedder_type: str = "api",
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: str = "12345678",
        neo4j_database: str = "papers",
        chunk_dir: str = "knowledge/chunkers/chunker_output/chapter",
    ):
        """
        初始化融合检索器
        
        Args:
            index_path: 向量索引目录（如 parent_child_api）
            embedder_type: embedding 类型
            neo4j_uri: Neo4j URI
            neo4j_user: Neo4j 用户名
            neo4j_password: Neo4j 密码
            neo4j_database: Neo4j 数据库名称
            chunk_dir: chunk 目录（供 KG 使用）
        """
        print("[FusionRetriever] 初始化中...")
        
        self.index_path = index_path
        
        # 初始化混合检索器（从索引加载）
        print("  [1/3] 初始化混合检索器...")
        self.hybrid_retriever = HybridRetriever(
            index_path=index_path,
            embedder_type=embedder_type,
        )
        
        # 初始化 KG 检索器
        print("  [2/3] 初始化 KG 检索器...")
        self.kg_retriever = KGRetriever(
            neo4j_uri=neo4j_uri,
            neo4j_user=neo4j_user,
            neo4j_password=neo4j_password,
            database=neo4j_database,
            chunk_dir=chunk_dir,
            embedder_type=embedder_type,
        )
        
        # 初始化 embedder（用于最终重排）
        print("  [3/3] 初始化 Embedder...")
        if embedder_type == "local":
            self.embedder = create_embedder(method="local", **Config.get_local_embedding_config())
        else:
            self.embedder = create_embedder(method=embedder_type)
        
        # 统计信息来自混合检索器
        hybrid_stats = self.hybrid_retriever.get_statistics()
        
        print("[FusionRetriever] 初始化完成")
        print(f"  - 文档数: {hybrid_stats.get('document_count')}")
        print(f"  - Embedder: {embedder_type}")
    
    def _deduplicate_documents(self, docs: List[str]) -> List[str]:
        """
        去重文档（保留顺序）
        
        Args:
            docs: 文档列表
            
        Returns:
            去重后的文档列表
        """
        seen = set()
        result = []
        for doc in docs:
            # 使用文档的前 100 个字符作为唯一标识
            doc_id = doc[:100] if len(doc) > 100 else doc
            if doc_id not in seen:
                seen.add(doc_id)
                result.append(doc)
        return result
    
    def _embed_with_retry(
        self,
        texts,
        max_retries: int = DEFAULT_RERANK_MAX_RETRIES,
        backoff_sec: float = DEFAULT_RERANK_BACKOFF_SEC,
    ) -> np.ndarray:
        """
        带重试的 embedding 调用，遇 429 等限流时指数退避重试。
        """
        last_error = None
        for attempt in range(max_retries):
            try:
                return self.embedder.embed(texts)
            except Exception as e:
                last_error = e
                msg = str(e).lower()
                # 仅对限流(429)或可重试错误重试
                if "429" in msg or "rate limit" in msg or "too many" in msg:
                    if attempt < max_retries - 1:
                        wait = backoff_sec * (2 ** attempt)
                        print(f"  [限流] 等待 {wait:.1f}s 后重试 ({attempt + 1}/{max_retries})")
                        time.sleep(wait)
                        continue
                raise
        raise last_error
    
    def _rerank_by_similarity(
        self, 
        query: str, 
        documents: List[str], 
        top_k: int,
        batch_size: int = 50,
        batch_delay_sec: float = DEFAULT_RERANK_BATCH_DELAY_SEC,
    ) -> List[Tuple[str, float]]:
        """
        使用 embedding 相似度重排（分批处理，带限流重试与批间延迟）
        
        Args:
            query: 查询文本
            documents: 文档列表
            top_k: 返回前 k 个
            batch_size: 批处理大小
            batch_delay_sec: 每批之间的延迟（秒），降低触发 429 的概率
            
        Returns:
            重排后的结果 [(document, score), ...]
        """
        if not documents:
            return []
        
        if len(documents) <= top_k:
            try:
                query_emb = self._embed_with_retry(query)
                if len(query_emb.shape) == 1:
                    query_emb = query_emb.reshape(1, -1)
                doc_embs = self._embed_with_retry(documents)
                similarities = cosine_similarity(query_emb, doc_embs)[0]
                return [(doc, float(score)) for doc, score in zip(documents, similarities)]
            except Exception as e:
                print(f"  [错误] Rerank 失败: {e}")
                return [(doc, 0.0) for doc in documents[:top_k]]
        
        print(f"  [Rerank] 对 {len(documents)} 个文档进行重排，返回 top {top_k}")
        
        try:
            query_emb = self._embed_with_retry(query)
            if len(query_emb.shape) == 1:
                query_emb = query_emb.reshape(1, -1)
            
            all_similarities = []
            num_batches = (len(documents) - 1) // batch_size + 1
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i+batch_size]
                if num_batches > 1:
                    print(f"    批次 {i//batch_size + 1}/{num_batches}")
                # 批前延迟（第一批后可加延迟，避免频率超限）
                if i > 0 and batch_delay_sec > 0:
                    time.sleep(batch_delay_sec)
                
                batch_embs = self._embed_with_retry(batch)
                batch_similarities = cosine_similarity(query_emb, batch_embs)[0]
                all_similarities.extend(batch_similarities)
            
            similarities = np.array(all_similarities)
            top_indices = np.argsort(similarities)[::-1][:top_k]
            return [(documents[idx], float(similarities[idx])) for idx in top_indices]
            
        except Exception as e:
            print(f"  [错误] Rerank 失败: {e}")
            print(f"  [回退] 返回前 {top_k} 个文档（未排序）")
            return [(doc, 0.0) for doc in documents[:top_k]]
    
    def retrieve(
        self, 
        query: str, 
        top_k: int = 5,
        hybrid_k: int = 10,
        kg_k: int = 10,
        use_kg: bool = True
    ) -> List[Tuple[str, float]]:
        """
        融合检索
        
        Args:
            query: 查询文本
            top_k: 最终返回结果数量
            hybrid_k: 混合检索返回数量
            kg_k: KG 检索返回数量
            use_kg: 是否使用 KG 检索
            
        Returns:
            [(document, score), ...] 按相似度排序
        """
        print(f"\n[FusionRetriever] 查询: {query}")
        print("=" * 80)
        
        all_documents = []
        
        # 1. 混合检索
        print(f"\n[1/{3 if use_kg else 2}] 混合检索（TF-IDF + Vector + RRF）")
        hybrid_results = self.hybrid_retriever.retrieve(query, top_k=hybrid_k)
        hybrid_docs = [doc for doc, _ in hybrid_results]
        all_documents.extend(hybrid_docs)
        print(f"  检索到 {len(hybrid_docs)} 个文档")
        
        # 2. KG 检索
        if use_kg:
            print(f"\n[2/3] KG 检索（jieba 分词 + 节点匹配）")
            try:
                kg_docs = self.kg_retriever.retrieve_documents(
                    query, 
                    max_neighbors=5, 
                    top_k=kg_k
                )
                all_documents.extend(kg_docs)
                print(f"  检索到 {len(kg_docs)} 个文档")
            except Exception as e:
                print(f"  [警告] KG 检索失败: {e}")
        
        # 3. 去重
        print(f"\n[{3 if use_kg else 2}/{3 if use_kg else 2}] 合并去重")
        print(f"  合并前: {len(all_documents)} 个文档")
        all_documents = self._deduplicate_documents(all_documents)
        print(f"  去重后: {len(all_documents)} 个文档")
        
        # 4. 统一重排
        if len(all_documents) > top_k:
            print(f"\n[最终] Embedding 相似度重排")
            final_results = self._rerank_by_similarity(query, all_documents, top_k)
        else:
            # 文档数量不多，直接计算分数
            final_results = self._rerank_by_similarity(query, all_documents, len(all_documents))
        
        print("\n" + "=" * 80)
        print(f"返回 {len(final_results)} 个最相关文档")
        
        return final_results
    
    def close(self):
        """关闭连接"""
        self.kg_retriever.close()
    
    def get_statistics(self) -> dict:
        """获取统计信息"""
        hybrid_stats = self.hybrid_retriever.get_statistics()
        kg_stats = {}
        try:
            kg_stats = self.kg_retriever.get_statistics()
        except Exception as e:
            kg_stats = {'error': str(e)}
        
        return {
            'retriever_type': 'fusion',
            'index_path': getattr(self, 'index_path', None),
            'num_documents': hybrid_stats.get('document_count'),
            'hybrid_stats': hybrid_stats,
            'kg_stats': kg_stats,
        }
