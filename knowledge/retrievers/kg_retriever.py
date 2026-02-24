"""
知识图谱检索器
基于 jieba 分词提取关键词，从 KG 中检索相关节点及其邻居对应的文本块
"""
import os
import time
import jieba
import numpy as np
from typing import List, Set
from neo4j import GraphDatabase
from sklearn.metrics.pairwise import cosine_similarity
from knowledge.embeddings import create_embedder
from config.config import Config

# 限流相关默认参数（与 FusionRetriever 保持风格一致）
KG_RERANK_MAX_RETRIES = 3
KG_RERANK_BACKOFF_SEC = 2.0
KG_RERANK_BATCH_DELAY_SEC = 1.0


class KGRetriever:
    """
    知识图谱检索器
    
    流程：
    1. 使用 jieba 分词提取查询中的关键词
    2. 在 KG 中匹配关键词对应的节点
    3. 获取节点及其一阶邻居
    4. 返回这些节点关联的文本块
    """
    
    def __init__(
        self,
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: str = "password",
        database: str = "papers",
        chunk_dir: str = "knowledge/chunkers/chunker_output/chapter",
        embedder_type: str = "api"
    ):
        """
        初始化 KG 检索器
        
        Args:
            neo4j_uri: Neo4j URI
            neo4j_user: Neo4j 用户名
            neo4j_password: Neo4j 密码
            database: Neo4j 数据库名称
            chunk_dir: chunk 文件目录
            embedder_type: embedding 类型（用于相似度排序）
        """
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        self.database = database
        self.chunk_dir = chunk_dir
        
        # 初始化 embedder（用于相似度排序）
        if embedder_type == "local":
            self.embedder = create_embedder(method="local", **Config.get_local_embedding_config())
        else:
            self.embedder = create_embedder(method=embedder_type)
        
        print(f"[KGRetriever] 初始化完成")
        print(f"  - 数据库: {database}")
        print(f"  - Chunk 目录: {chunk_dir}")
        print(f"  - Embedder: {embedder_type}")
    
    def extract_keywords(self, query: str, top_k: int = 5) -> List[str]:
        """
        使用 jieba 分词提取关键词
        
        Args:
            query: 查询文本
            top_k: 最多提取多少个关键词
            
        Returns:
            关键词列表
        """
        # 使用 jieba 分词
        words = jieba.cut(query)
        
        # 过滤停用词和标点
        stopwords = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', 
                    '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', 
                    '会', '着', '没有', '看', '好', '自己', '这', '？', '，', '。', 
                    '！', '、', '：', '；', '"', '"', ''', ''', '（', '）', '《', '》'}
        
        keywords = []
        for word in words:
            word = word.strip()
            # 过滤：长度 >= 2，不是停用词，不是纯数字
            if len(word) >= 2 and word not in stopwords and not word.isdigit():
                keywords.append(word)
        
        # 去重并限制数量
        keywords = list(dict.fromkeys(keywords))[:top_k]
        
        return keywords
    
    def retrieve_related_chunks(self, query: str, max_neighbors: int = 5) -> Set[str]:
        """
        从 KG 中检索相关的 chunk 文件
        
        Args:
            query: 查询文本
            max_neighbors: 每个节点最多返回多少个邻居
            
        Returns:
            相关的 chunk 文件名集合
        """
        # 1. 提取关键词
        keywords = self.extract_keywords(query)
        
        if not keywords:
            print(f"  [KG] 未提取到关键词")
            return set()
        
        print(f"  [KG] 提取关键词: {keywords}")
        
        # 2. 从 KG 中检索
        chunk_files = set()
        
        with self.driver.session(database=self.database) as session:
            for keyword in keywords:
                # 精确匹配关键词的节点
                query_cypher = """
                MATCH (e:Entity)
                WHERE e.name = $keyword
                OPTIONAL MATCH (e)-[r]-(neighbor:Entity)
                WITH e, collect(DISTINCT neighbor)[0..$max_neighbors] as neighbors
                RETURN e.chunk_files as entity_chunks, 
                       [n IN neighbors | n.chunk_files] as neighbor_chunks
                """
                
                result = session.run(
                    query_cypher, 
                    keyword=keyword, 
                    max_neighbors=max_neighbors
                )
                
                for record in result:
                    # 添加匹配节点的 chunks
                    if record['entity_chunks']:
                        chunk_files.update(record['entity_chunks'])
                    
                    # 添加邻居节点的 chunks
                    if record['neighbor_chunks']:
                        for neighbor_chunk_list in record['neighbor_chunks']:
                            if neighbor_chunk_list:
                                chunk_files.update(neighbor_chunk_list)
        
        print(f"  [KG] 检索到 {len(chunk_files)} 个相关 chunks")
        
        return chunk_files
    
    def _embed_with_retry(
        self,
        texts,
        max_retries: int = KG_RERANK_MAX_RETRIES,
        backoff_sec: float = KG_RERANK_BACKOFF_SEC,
    ) -> np.ndarray:
        """
        带重试的 embedding 调用，主要针对 429 限流错误做指数退避。
        """
        last_error = None
        for attempt in range(max_retries):
            try:
                return self.embedder.embed(texts)
            except Exception as e:
                last_error = e
                msg = str(e).lower()
                # 仅对限流 / 频率过高类错误重试
                if "429" in msg or "rate limit" in msg or "too many" in msg:
                    if attempt < max_retries - 1:
                        wait = backoff_sec * (2 ** attempt)
                        print(f"  [KG][限流] 等待 {wait:.1f}s 后重试 ({attempt + 1}/{max_retries})")
                        time.sleep(wait)
                        continue
                # 其他错误直接抛出
                raise
        raise last_error

    def _rank_by_similarity(self, query: str, documents: List[str], top_k: int, batch_size: int = 50) -> List[str]:
        """
        使用 embedding 相似度对文档排序（分批处理）
        
        Args:
            query: 查询文本
            documents: 文档列表
            top_k: 返回前 k 个
            batch_size: 批处理大小（避免 API 限制）
            
        Returns:
            排序后的前 k 个文档
        """
        if not documents:
            return []
        
        if len(documents) <= top_k:
            # 文档数量不多时，直接返回（避免额外 embedding 调用）
            return documents
        
        print(f"  [KG] 使用 embedding 相似度排序，从 {len(documents)} 个中选出 top {top_k}")
        
        try:
            # 计算查询的 embedding
            query_emb = self._embed_with_retry(query)
            if len(query_emb.shape) == 1:
                query_emb = query_emb.reshape(1, -1)
            
            # 分批处理文档
            all_similarities = []
            num_batches = (len(documents) - 1) // batch_size + 1
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i+batch_size]
                print(f"    处理第 {i//batch_size + 1} 批 ({len(batch)} 个文档)")
                # 批间延迟，降低触发 429 的概率
                if i > 0 and KG_RERANK_BATCH_DELAY_SEC > 0:
                    time.sleep(KG_RERANK_BATCH_DELAY_SEC)
                
                # 计算这一批的 embedding
                batch_embs = self._embed_with_retry(batch)
                
                # 计算相似度
                batch_similarities = cosine_similarity(query_emb, batch_embs)[0]
                all_similarities.extend(batch_similarities)
            
            # 转换为 numpy 数组
            similarities = np.array(all_similarities)
            
            # 排序并返回 top_k
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            return [documents[idx] for idx in top_indices]
            
        except Exception as e:
            print(f"  [错误] 相似度排序失败: {e}")
            print(f"  [回退] 返回前 {top_k} 个文档（未排序）")
            return documents[:top_k]
    
    def retrieve_documents(self, query: str, max_neighbors: int = 5, top_k: int = 5) -> List[str]:
        """
        检索相关文档内容
        
        Args:
            query: 查询文本
            max_neighbors: 每个节点最多返回多少个邻居
            top_k: 返回前 k 个最相关的文档
            
        Returns:
            文档内容列表（按相似度排序）
        """
        # 获取 chunk 文件名
        chunk_files = self.retrieve_related_chunks(query, max_neighbors)
        
        # 读取文档内容
        documents = []
        for chunk_file in chunk_files:
            filepath = os.path.join(self.chunk_dir, chunk_file)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if content.strip():
                            documents.append(content)
                except Exception as e:
                    print(f"  [警告] 读取文件失败: {chunk_file} - {e}")
        
        # 使用相似度排序并返回 top_k
        if documents:
            return self._rank_by_similarity(query, documents, top_k)
        
        return []
    
    def close(self):
        """关闭连接"""
        self.driver.close()
    
    def get_statistics(self) -> dict:
        """获取统计信息"""
        with self.driver.session(database=self.database) as session:
            # 统计节点数
            node_count = session.run("MATCH (n:Entity) RETURN count(n) as count").single()['count']
            
            # 统计关系数
            rel_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()['count']
            
            return {
                'retriever_type': 'kg',
                'database': self.database,
                'node_count': node_count,
                'relation_count': rel_count,
                'chunk_dir': self.chunk_dir
            }
