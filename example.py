"""
使用示例
演示如何使用束流数据查询系统
"""

from agents import BeamDataAgent
from config import Config
from tools import query_beam_data, get_data_info


def example_1_direct_tool_call():
    """示例1：直接调用工具函数"""
    print("=" * 60)
    print("示例1：直接调用工具函数")
    print("=" * 60)
    
    # 1. 查询数据概要
    print("\n1. 查询数据概要信息：")
    info = get_data_info()
    print(f"  - 总记录数: {info['total_records']}")
    print(f"  - 时间范围: {info['time_range']['start']} 至 {info['time_range']['end']}")
    print(f"  - target均值: {info['target_stats']['mean']:.4f}")
    
    # 2. 查询特定时间范围的数据
    print("\n2. 查询特定时间范围的数据：")
    result = query_beam_data(
        start_time="2025-08-30 17:23:26",
        end_time="2025-08-30 17:23:35",
        columns=["时间", "target"]
    )
    
    if result['success']:
        print(f"  - 查询成功！")
        print(f"  - 返回记录数: {result['count']}")
        print(f"  - target平均值: {result['statistics']['target_mean']:.4f}")
        print(f"  - 前3条数据:")
        for i, record in enumerate(result['data'][:3]):
            print(f"    [{i+1}] 时间: {record['时间']}, target: {record['target']:.4f}")
    else:
        print(f"  - 查询失败: {result['error']}")


def example_2_agent_interaction():
    """示例2：使用代理进行自然语言交互"""
    print("\n\n" + "=" * 60)
    print("示例2：使用代理进行自然语言交互")
    print("=" * 60)
    
    # 初始化代理
    config = Config.get_api_config()
    agent = BeamDataAgent(
        api_key=config['api_key'],
        base_url=config['base_url'],
        model=config['model']
    )
    
    # 测试对话
    test_queries = [
        "束流数据集有多少条记录？",
        "查询2025年8月30日17点23分26秒到17点24分30秒的束流数据，只用取target列以及feature1-feature5列",
        "这段时间的target平均值是多少？"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n[对话 {i}]")
        print(f"用户: {query}")
        print(f"助手: ", end="")
        response = agent.chat(query)
        print(response)


def example_3_error_handling():
    """示例3：错误处理"""
    print("\n\n" + "=" * 60)
    print("示例3：错误处理示例")
    print("=" * 60)
    
    # 测试错误的时间格式
    print("\n1. 测试无效的时间格式：")
    result = query_beam_data(
        start_time="invalid-time",
        end_time="2025-08-30 17:23:30"
    )
    print(f"  - 成功: {result['success']}")
    if not result['success']:
        print(f"  - 错误信息: {result['message']}")
    
    # 测试不存在的时间范围
    print("\n2. 测试不存在的时间范围：")
    result = query_beam_data(
        start_time="2026-01-01 00:00:00",
        end_time="2026-01-01 01:00:00"
    )
    print(f"  - 成功: {result['success']}")
    print(f"  - 返回记录数: {result['count']}")


def main():
    """运行所有示例"""
    print("\n" + "╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "束流数据查询系统 - 使用示例" + " " * 15 + "║")
    print("╚" + "═" * 58 + "╝\n")
    
    try:
        # 示例1：直接调用工具函数
        example_1_direct_tool_call()
        
        # 示例2：使用代理进行自然语言交互（需要API）
        print("\n\n是否运行示例2（需要调用API）？(y/n): ", end="")

        choice = input().strip().lower()
        if choice == 'y':
            example_2_agent_interaction()

        
        # 示例3：错误处理
        example_3_error_handling()
        
        print("\n\n" + "=" * 60)
        print("所有示例运行完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

