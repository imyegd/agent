"""
测试 HybridRetriever 混合检索器
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from knowledge.retrievers.hybrid_retriever import HybridRetriever


def test_hybrid():
    print("=" * 80)
    print("测试 HybridRetriever")
    print("=" * 80)
    
    index_path = "knowledge/vector_store/index/parent_child_api"
    
    print(f"\n索引路径: {index_path}")
    
    # 初始化检索器
    print("\n初始化混合检索器...")
    retriever = HybridRetriever(
        index_path=index_path,
        embedder_type="api",
        rrf_k=60
    )
    
    print("\n[成功] 检索器初始化成功!")
    
    # 统计信息
    print("\n统计信息:")
    stats = retriever.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 测试查询
    print("\n" + "=" * 80)
    print("测试检索")
    print("=" * 80)
    
    queries = [
        "束流加速器的原理是什么"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n查询 {i}: {query}")
        print("-" * 80)
        
        results = retriever.retrieve(query, top_k=3)
        
        for j, (doc, score) in enumerate(results, 1):
            print(f'len(doc): {len(doc)}')
            try:
                preview = doc[:150].replace('\n', ' ').replace('\r', '')
                if len(doc) > 150:
                    preview += "..."
                print(f"\n  {j}. 分数: {score:.4f}")
                print(f"     {preview}")
            except:
                print(f"\n  {j}. 分数: {score:.4f}")
                print(f"     [无法显示内容]")
    
    print("\n" + "=" * 80)
    print("测试完成!")
    print("=" * 80)


if __name__ == "__main__":
    test_hybrid()
