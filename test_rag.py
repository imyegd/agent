"""
测试 RAG 知识增强系统
"""
import sys
import io

# 设置 UTF-8 编码输出
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
except:
    pass

from knowledge import search_knowledge, explain_features, get_troubleshooting_solutions


def test_knowledge_base_loading():
    """测试知识库加载"""
    print("=" * 70)
    print("测试1: 知识库加载")
    print("=" * 70)
    
    from knowledge import KnowledgeBase
    kb = KnowledgeBase()
    stats = kb.get_statistics()
    
    print(f"✓ 特征定义数量: {stats['features_count']}")
    print(f"✓ 解决方案数量: {stats['solutions_count']}")
    print(f"✓ 领域概念数量: {stats['concepts_count']}")
    print()


def test_feature_explanation():
    """测试特征解释功能"""
    print("=" * 70)
    print("测试2: 特征解释")
    print("=" * 70)
    
    result = explain_features(['feature1', 'feature3', 'feature8'])
    
    if result['success']:
        print(f"✓ 成功解释 {result['feature_count']} 个特征\n")
        
        for feat_name, feat_info in result['features'].items():
            print(f"【{feat_name}】")
            print(f"  名称: {feat_info['name']}")
            print(f"  描述: {feat_info['description'][:50]}...")
            print(f"  相关系统: {feat_info['related_to']}")
            print()
    else:
        print(f"✗ 失败: {result['message']}")
    print()


def test_knowledge_search():
    """测试知识检索功能"""
    print("=" * 70)
    print("测试3: 知识检索")
    print("=" * 70)
    
    # 测试查询
    queries = [
        ("电压传感器异常", None),
        ("T2统计量", "concept"),
        ("真空系统故障", "solution")
    ]
    
    for query, doc_type in queries:
        print(f"\n查询: '{query}' (类型: {doc_type or '全部'})")
        result = search_knowledge(query, top_k=2, doc_type=doc_type)
        
        if result['success']:
            print(f"✓ 找到 {result['results_count']} 个相关结果:")
            for i, r in enumerate(result['results'], 1):
                print(f"  {i}. [评分: {r['score']:.3f}] {r['content'][:80]}...")
        else:
            print(f"✗ 失败: {result['message']}")
    print()


def test_solution_search():
    """测试解决方案搜索"""
    print("=" * 70)
    print("测试4: 解决方案搜索")
    print("=" * 70)
    
    result = get_troubleshooting_solutions(
        problem_description="束流强度不稳定",
        feature_names=['feature3']
    )
    
    if result['success']:
        print(f"✓ 找到 {result['solutions_count']} 个解决方案\n")
        
        for i, sol in enumerate(result['solutions'], 1):
            print(f"【方案 {i}】")
            print(f"  问题: {sol['problem']}")
            print(f"  优先级: {sol['priority']}")
            print(f"  根本原因: {sol['root_causes'][:2]}")  # 只显示前2个
            print(f"  解决方案: {sol['solutions'][:2]}")  # 只显示前2个
            print()
    else:
        print(f"✗ 失败: {result['message']}")
    print()


def test_pls_with_rag():
    """测试 PLS 分析与 RAG 集成"""
    print("=" * 70)
    print("测试5: PLS 分析 + 知识增强")
    print("=" * 70)
    
    from tools.pls_analysis import analyze_beam_fluctuation
    
    result = analyze_beam_fluctuation(
        start_time="2025-08-30 17:23:26",
        end_time="2025-08-31 21:23:59"
    )
    
    if result.get('success'):
        print("✓ PLS 分析成功")
        print(f"  数据条数: {result['data_count']}")
        print(f"  异常点数: {result['anomaly_detection']['anomaly_count']}")
        print(f"  异常率: {result['anomaly_detection']['anomaly_rate']:.2%}")
        
        # 检查知识增强
        if 'knowledge_enhanced' in result:
            print("\n✓ 知识增强成功!")
            ke = result['knowledge_enhanced']
            
            if ke.get('summary'):
                print(f"\n知识摘要:\n  {ke['summary']}")
            
            if ke.get('feature_explanations'):
                print(f"\n特征解释数量: {len(ke['feature_explanations'])}")
                # 显示第一个特征
                for feat_name, feat_info in list(ke['feature_explanations'].items())[:1]:
                    if feat_name != 'related_features':
                        print(f"  示例 - {feat_name}: {feat_info.get('name', '')} - {feat_info.get('impact', '')[:50]}...")
            
            if ke.get('solutions'):
                print(f"\n推荐解决方案数量: {len(ke['solutions'])}")
                if ke['solutions']:
                    sol = ke['solutions'][0]
                    print(f"  示例 - {sol.get('problem', '')}")
                    print(f"    优先级: {sol.get('priority', '')}")
        else:
            print("\n⚠ 未检测到知识增强（可能没有异常或RAG未启用）")
    else:
        print(f"✗ 分析失败: {result.get('message')}")
    print()


def test_tool_registration():
    """测试工具注册"""
    print("=" * 70)
    print("测试6: 工具注册验证")
    print("=" * 70)
    
    from tools import TOOLS, TOOL_FUNCTIONS
    
    print(f"✓ 总工具数: {len(TOOLS)}")
    print(f"✓ 函数映射数: {len(TOOL_FUNCTIONS)}")
    
    # 检查 RAG 工具是否注册
    rag_tools = [t['function']['name'] for t in TOOLS 
                 if t['function']['name'] in ['search_knowledge', 'explain_features', 'get_troubleshooting_solutions']]
    
    if rag_tools:
        print(f"\n✓ RAG 工具已注册: {', '.join(rag_tools)}")
    else:
        print("\n⚠ RAG 工具未注册")
    
    print("\n所有工具列表:")
    for t in TOOLS:
        name = t['function']['name']
        desc = t['function']['description'][:50]
        print(f"  - {name}: {desc}...")
    print()


if __name__ == "__main__":
    print("\n")
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║        RAG 知识增强系统测试                                ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print()
    
    try:
        test_knowledge_base_loading()
        test_feature_explanation()
        test_knowledge_search()
        test_solution_search()
        test_pls_with_rag()
        test_tool_registration()
        
        print("=" * 70)
        print("✓ 所有测试完成！")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()

