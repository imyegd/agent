"""测试检索器的脚本"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge import OnlineRetriever, search_knowledge


def test_basic_retrieval():
    """测试基本检索功能"""
    print("="*60)
    print("测试基本检索")
    print("="*60 + "\n")
    
    retriever = OnlineRetriever()
    
    # 统计信息
    stats = retriever.get_stats()
    print(f"索引统计:")
    print(f"  文档数: {stats['total_documents']}")
    print(f"  维度: {stats['dimension']}")
    print(f"  来源文件: {stats.get('source_file_count', 0)}")
    
    # 测试查询
    queries = [
        "束流强度测量方法",
        "二次束流",
        "加速器真空系统",
    ]
    
    for query in queries:
        print(f"\n{'='*60}")
        print(f"查询: {query}")
        print("="*60)
        
        results = retriever.search(query, top_k=3)
        
        for i, result in enumerate(results, 1):
            doc = result['document']
            score = result['score']
            source = result.get('metadata', {}).get('source_file', 'Unknown')
            
            # 截断显示
            preview = doc[:120] + "..." if len(doc) > 120 else doc
            
            print(f"\n[{i}] 相似度: {score:.4f} | 来源: {source}")
            print(f"    {preview}")


def test_rag_tool():
    """测试RAG工具函数"""
    print("\n" + "="*60)
    print("测试RAG工具函数")
    print("="*60 + "\n")
    
    # 测试知识搜索
    result = search_knowledge("束流不稳定的原因", top_k=3)
    
    print(f"检索成功: {result['success']}")
    print(f"数据源: {result.get('source', 'Unknown')}")
    print(f"结果数: {result['results_count']}")
    
    if result['results_count'] > 0:
        print("\n前2个结果:")
        for i, r in enumerate(result['results'][:2], 1):
            content = r['content'][:100] + "..." if len(r['content']) > 100 else r['content']
            print(f"\n[{i}] 分数: {r['score']:.4f}")
            print(f"    {content}")


def main():
    """主函数"""
    try:
        test_basic_retrieval()
        test_rag_tool()
        
        print("\n" + "="*60)
        print("测试完成!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

