"""
检索器工厂
"""
from typing import List, Dict
import sys
import os

# 处理导入路径
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from knowledge.retrievers.base_retriever import BaseRetriever
    from knowledge.retrievers.keyword_retriever import KeywordRetriever
    from knowledge.retrievers.vector_retriever import VectorRetriever
    from knowledge.retrievers.hybrid_retriever import HybridRetriever
else:
    from .base_retriever import BaseRetriever
    from .keyword_retriever import KeywordRetriever
    from .vector_retriever import VectorRetriever
    from .hybrid_retriever import HybridRetriever


class RetrieverFactory:
    """检索器工厂类"""
    
    @staticmethod
    def create_retriever(
        retriever_type: str,
        documents: List[str],
        **kwargs
    ) -> BaseRetriever:
        """
        创建指定类型的检索器
        
        Args:
            retriever_type: 检索器类型，可选 "keyword", "vector", "hybrid"
            documents: 文档列表
            **kwargs: 传递给检索器的参数
            
                对于 keyword:
                    - max_features: TF-IDF 最大特征数 (默认 5000)
                    - ngram_range: N-gram 范围 (默认 (1, 2))
                    - min_df: 最小文档频率 (默认 1)
                
                对于 vector:
                    - embedder_type: 向量化方法 (默认 "api")
                    - 其他 embedder 相关参数
                
                对于 hybrid:
                    - embedder_type: 向量化方法 (默认 "api")
                    - rrf_k: RRF 平滑常数 (默认 60)
                    - max_features: TF-IDF 最大特征数 (默认 5000)
                    - ngram_range: N-gram 范围 (默认 (1, 2))
            
        Returns:
            检索器实例
        """
        if retriever_type == "keyword":
            return KeywordRetriever(
                documents=documents,
                max_features=kwargs.get('max_features', 5000),
                ngram_range=kwargs.get('ngram_range', (1, 2)),
                min_df=kwargs.get('min_df', 1)
            )
        
        elif retriever_type == "vector":
            return VectorRetriever(
                documents=documents,
                embedder_type=kwargs.get('embedder_type', 'api'),
                **{k: v for k, v in kwargs.items() if k != 'embedder_type'}
            )
        
        elif retriever_type == "hybrid":
            return HybridRetriever(
                documents=documents,
                embedder_type=kwargs.get('embedder_type', 'api'),
                rrf_k=kwargs.get('rrf_k', 60),
                max_features=kwargs.get('max_features', 5000),
                ngram_range=kwargs.get('ngram_range', (1, 2)),
                **{k: v for k, v in kwargs.items() if k not in ['embedder_type', 'rrf_k', 'max_features', 'ngram_range']}
            )
        
        else:
            raise ValueError(f"未知的检索器类型: {retriever_type}")
    
    @staticmethod
    def get_available_retrievers() -> Dict[str, str]:
        """
        获取可用的检索器类型
        
        Returns:
            检索器类型及描述
        """
        return {
            "keyword": "关键词检索 (TF-IDF) - 精确关键词匹配，速度快",
            "vector": "向量检索 (语义) - 理解语义和上下文，支持同义词",
            "hybrid": "混合检索 (RRF) - 综合关键词和语义检索，鲁棒性强"
        }


# 便捷函数
def create_retriever(
    retriever_type: str,
    documents: List[str],
    **kwargs
) -> BaseRetriever:
    """
    便捷函数：创建检索器
    
    Args:
        retriever_type: 检索器类型 ("keyword", "vector", "hybrid")
        documents: 文档列表
        **kwargs: 传递给检索器的参数
        
    Returns:
        检索器实例
    
    Examples:
        >>> # 创建关键词检索器
        >>> keyword_retriever = create_retriever("keyword", documents)
        
        >>> # 创建向量检索器（使用 API）
        >>> vector_retriever = create_retriever("vector", documents, embedder_type="api")
        
        >>> # 创建混合检索器
        >>> hybrid_retriever = create_retriever("hybrid", documents, embedder_type="local")
    """
    return RetrieverFactory.create_retriever(retriever_type, documents, **kwargs)


if __name__ == "__main__":
    # 测试示例
    test_docs = [
        "加速器束流强度测量系统的研究与应用",
        "重离子加速器在医学领域的应用研究",
        "BEPCII 加速器的主要特点和技术指标",
        "质子加速器能量可以达到 100 MeV 的技术突破"
    ]
    
    print("=" * 80)
    print("测试检索器工厂")
    print("=" * 80)
    
    print("\n可用检索器:")
    for name, desc in RetrieverFactory.get_available_retrievers().items():
        print(f"  - {name}: {desc}")
    
    # 测试关键词检索
    print("\n" + "=" * 80)
    print("[1] 测试关键词检索")
    print("=" * 80)
    keyword_retriever = create_retriever("hybrid", test_docs, embedder_type="api")
    results = keyword_retriever.retrieve("加速器束流", top_k=2)
    print(f"\n检索结果 (查询: '加速器束流'):")
    for i, (doc, score) in enumerate(results, 1):
        print(f"  {i}. {doc}")
        print(f"     Score: {score:.4f}")
    
    print(f"\n统计信息:")
    stats = keyword_retriever.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
