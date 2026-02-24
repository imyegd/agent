"""
测试 VectorRetriever 向量检索器
从 parent_child_api 索引加载并测试检索能力
"""
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from knowledge.retrievers.vector_retriever import VectorRetriever


def test_vector_retriever():
    """测试向量检索器"""
    
    print("=" * 80)
    print("测试 VectorRetriever - 向量检索器")
    print("=" * 80)
    
    # 索引路径
    index_path = "knowledge/vector_store/index/parent_child_api"
    
    if not os.path.exists(index_path):
        print(f"错误: 索引路径不存在 - {index_path}")
        return
    
    print(f"\n索引路径: {index_path}")
    print(f"索引文件:")
    for file in os.listdir(index_path):
        file_path = os.path.join(index_path, file)
        file_size = os.path.getsize(file_path) / 1024  # KB
        print(f"  - {file} ({file_size:.2f} KB)")
    
    # 初始化检索器
    print("\n" + "=" * 80)
    print("初始化向量检索器...")
    print("=" * 80)
    
    try:
        retriever = VectorRetriever(
            index_path=index_path,
            embedder_type="api"  # 使用 API embedder
        )
        
        print("\n[成功] 检索器初始化成功!")
        
    except Exception as e:
        print(f"\n[失败] 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 显示统计信息
    print("\n" + "=" * 80)
    print("检索器统计信息")
    print("=" * 80)
    
    stats = retriever.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 测试查询
    print("\n" + "=" * 80)
    print("测试检索功能")
    print("=" * 80)
    
    # 定义测试查询
    test_queries = [
        "什么是机器学习?",
        "深度学习的基本原理",
        "如何训练神经网络?",
        "什么是卷积神经网络?",
        "自然语言处理的应用"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'─' * 80}")
        print(f"查询 {i}: {query}")
        print(f"{'─' * 80}")
        
        try:
            # 执行检索
            results = retriever.retrieve(query, top_k=3)
            
            if not results:
                print("  未找到相关结果")
                continue
            
            # 显示结果
            for j, (doc, score) in enumerate(results, 1):
                print(f"\n  结果 {j} (相似度: {score:.4f}):")
                print(f"  {'─' * 76}")
                
                # 显示文档内容（限制长度）
                doc_preview = doc[:200] + "..." if len(doc) > 200 else doc
                print(f"  {doc_preview}")
                
        except Exception as e:
            print(f"\n  [失败] 检索失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("测试完成!")
    print("=" * 80)


if __name__ == "__main__":
    test_vector_retriever()
