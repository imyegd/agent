"""
知识检索器
"""
from typing import List, Dict, Any, Optional
import numpy as np
from .knowledge_base import KnowledgeBase
from .embeddings import SimpleEmbedder, create_embedder


class KnowledgeRetriever:
    """知识检索器 - 使用向量相似度检索相关知识"""
    
    def __init__(
        self, 
        knowledge_base: Optional[KnowledgeBase] = None,
        embedder_type: str = "simple",
        **embedder_kwargs
    ):
        """
        初始化检索器
        
        Args:
            knowledge_base: 知识库实例，默认创建新实例
            embedder_type: 向量化方法，可选 "simple", "api", "hybrid"
            **embedder_kwargs: 传递给embedder的参数
        """
        self.kb = knowledge_base or KnowledgeBase()
        self.embedder = create_embedder(embedder_type, **embedder_kwargs)
        
        self.documents = []
        self.doc_embeddings = None
        
        self._build_index()
    
    def _build_index(self):
        """构建文档向量索引"""
        print("正在构建知识库索引...")
        
        # 获取所有文档
        docs_with_metadata = self.kb.get_all_documents()
        self.documents = docs_with_metadata
        
        if not self.documents:
            print("警告: 知识库为空")
            return
        
        # 提取文本
        doc_texts = [doc["text"] for doc in self.documents]
        
        # 向量化文档
        if hasattr(self.embedder, 'fit'):
            self.embedder.fit(doc_texts)
        
        self.doc_embeddings = self.embedder.embed(doc_texts)
        
        print(f"索引构建完成，共 {len(self.documents)} 个文档")
    
    def search(
        self, 
        query: str, 
        top_k: int = 5,
        doc_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        检索相关知识
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            doc_type: 文档类型过滤，可选 "feature", "solution", "concept"
            
        Returns:
            检索结果列表，每个结果包含document, score, metadata
        """
        if self.doc_embeddings is None or len(self.documents) == 0:
            return []
        
        # 向量化查询
        query_embedding = self.embedder.embed(query)
        
        # 计算余弦相似度
        # 归一化
        query_norm = query_embedding / (np.linalg.norm(query_embedding, axis=1, keepdims=True) + 1e-10)
        doc_norms = self.doc_embeddings / (np.linalg.norm(self.doc_embeddings, axis=1, keepdims=True) + 1e-10)
        
        # 计算相似度
        similarities = np.dot(doc_norms, query_norm.T).flatten()
        
        # 根据文档类型过滤
        if doc_type:
            indices = [i for i, doc in enumerate(self.documents) 
                      if doc["metadata"].get("type") == doc_type]
            filtered_similarities = similarities[indices]
            filtered_docs = [self.documents[i] for i in indices]
        else:
            filtered_similarities = similarities
            filtered_docs = self.documents
            indices = list(range(len(self.documents)))
        
        # 排序并获取top_k
        if len(filtered_similarities) == 0:
            return []
        
        top_indices = np.argsort(filtered_similarities)[-top_k:][::-1]
        
        # 构建结果
        results = []
        for idx in top_indices:
            doc = filtered_docs[idx]
            score = float(filtered_similarities[idx])
            
            results.append({
                "document": doc["text"],
                "score": score,
                "metadata": doc["metadata"]
            })
        
        return results
    
    def get_feature_explanations(
        self, 
        feature_names: List[str],
        include_related: bool = True
    ) -> Dict[str, Any]:
        """
        获取特征的详细解释
        
        Args:
            feature_names: 特征名称列表
            include_related: 是否包含相关特征推荐
            
        Returns:
            特征解释字典
        """
        explanations = {}
        
        # 直接从知识库获取
        for feat_name in feature_names:
            info = self.kb.get_feature_info(feat_name)
            if info:
                explanations[feat_name] = info
        
        # 如果需要，搜索相关特征
        if include_related and feature_names:
            query = " ".join([self.kb.get_feature_info(f).get("name", f) 
                             for f in feature_names if self.kb.get_feature_info(f)])
            
            if query:
                related = self.search(query, top_k=3, doc_type="feature")
                explanations["related_features"] = [
                    r["metadata"]["name"] for r in related 
                    if r["metadata"].get("name") not in feature_names
                ]
        
        return explanations
    
    def find_solutions(
        self, 
        problem_description: str,
        feature_names: Optional[List[str]] = None,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        根据问题描述和相关特征查找解决方案
        
        Args:
            problem_description: 问题描述
            feature_names: 相关特征名称列表
            top_k: 返回结果数量
            
        Returns:
            解决方案列表
        """
        # 构建增强查询
        query_parts = [problem_description]
        
        if feature_names:
            for feat_name in feature_names:
                info = self.kb.get_feature_info(feat_name)
                if info:
                    query_parts.append(info.get("name", ""))
                    query_parts.append(info.get("related_to", ""))
        
        query = " ".join(query_parts)
        
        # 搜索解决方案
        results = self.search(query, top_k=top_k, doc_type="solution")
        
        # 提取解决方案详情
        solutions = []
        for result in results:
            solution_data = result["metadata"].get("source", {})
            solution_data["relevance_score"] = result["score"]
            solutions.append(solution_data)
        
        return solutions
    
    def search_concepts(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        搜索领域概念
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            
        Returns:
            概念列表
        """
        results = self.search(query, top_k=top_k, doc_type="concept")
        
        concepts = []
        for result in results:
            concept_data = result["metadata"].get("source", {})
            concept_data["relevance_score"] = result["score"]
            concepts.append(concept_data)
        
        return concepts
    
    def get_recommendations(self, anomaly_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据异常信息获取综合建议
        
        Args:
            anomaly_info: 异常信息，包含特征名称、统计量等
            
        Returns:
            包含解释、解决方案、相关概念的综合建议
        """
        recommendations = {
            "feature_explanations": {},
            "solutions": [],
            "relevant_concepts": [],
            "summary": ""
        }
        
        # 提取异常特征
        feature_names = []
        if "T2X_top_features" in anomaly_info:
            feature_names.extend(anomaly_info["T2X_top_features"].keys())
        if "SPEX_top_features" in anomaly_info:
            feature_names.extend(anomaly_info["SPEX_top_features"].keys())
        
        feature_names = list(set(feature_names))[:5]  # 最多取5个
        
        if feature_names:
            # 获取特征解释
            recommendations["feature_explanations"] = self.get_feature_explanations(
                feature_names, 
                include_related=False
            )
            
            # 查找解决方案
            problem_desc = f"异常检测 {', '.join(feature_names)} 异常"
            recommendations["solutions"] = self.find_solutions(
                problem_desc, 
                feature_names, 
                top_k=3
            )
            
            # 搜索相关概念
            if anomaly_info.get("T2X_anomaly"):
                concepts = self.search_concepts("T2统计量 异常", top_k=1)
                recommendations["relevant_concepts"].extend(concepts)
            
            if anomaly_info.get("SPEX_anomaly"):
                concepts = self.search_concepts("SPE统计量 异常", top_k=1)
                recommendations["relevant_concepts"].extend(concepts)
            
            # 生成摘要
            feature_info = recommendations["feature_explanations"]
            feature_summaries = []
            for feat_name in feature_names:
                if feat_name in feature_info:
                    info = feature_info[feat_name]
                    feature_summaries.append(
                        f"{feat_name}({info.get('name', '')}): {info.get('impact', '')}"
                    )
            
            recommendations["summary"] = (
                f"检测到异常，主要涉及特征: {', '.join(feature_names)}。" +
                " ".join(feature_summaries[:2])  # 只显示前2个特征的详情
            )
        
        return recommendations

