"""
完整实验流程

自动化执行：
1. 生成问答数据集
2. 评估检索效果
3. 生成对比报告
"""
import os
import sys
import argparse

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from experiment.generate_questions import generate_qa_dataset
from experiment.evaluate_chunkers import load_qa_dataset, evaluate_retrieval, generate_comparison_report


def run_full_experiment(num_fragments: int = 5,
                       questions_per_fragment: int = 3,
                       fragment_length: int = 1000,
                       chunker_types: list = None,
                       embedder_type: str = "api",
                       top_k: int = 5,
                       request_delay: int = 3):
    """
    运行完整实验
    
    Args:
        num_fragments: 文本片段数量（实际生成500个时改这个参数）
        questions_per_fragment: 每个片段生成的问题数量
        fragment_length: 片段长度
        chunker_types: 要评估的 chunker 类型列表
        embedder_type: embedder 类型
        top_k: 检索返回前 k 个结果
        request_delay: API 请求间隔（秒），避免限流
    """
    if chunker_types is None:
        chunker_types = ["fixed", "semantic", "chapter"]
    
    print("=" * 80)
    print("Chunker 方法对比实验")
    print("=" * 80)
    print(f"\n实验参数:")
    print(f"  文本片段数: {num_fragments}")
    print(f"  每片段问题数: {questions_per_fragment}")
    print(f"  片段长度: {fragment_length}")
    print(f"  Chunker 类型: {', '.join(chunker_types)}")
    print(f"  Embedder 类型: {embedder_type}")
    print(f"  Top-K: {top_k}")
    print(f"  请求延迟: {request_delay} 秒")
    
    # # 步骤 1: 生成问答数据集
    # print("\n" + "=" * 80)
    # print("步骤 1: 生成问答数据集")
    # print("=" * 80)
    
    # generate_qa_dataset(
    #     num_fragments=num_fragments,
    #     questions_per_fragment=questions_per_fragment,
    #     fragment_length=fragment_length,
    #     chunker_types=chunker_types,
    #     output_file="experiment/data/qa_dataset.json",
    #     request_delay=request_delay
    # )
    
    # 步骤 2: 加载数据集
    print("\n" + "=" * 80)
    print("步骤 2: 加载数据集")
    print("=" * 80)
    
    dataset = load_qa_dataset("experiment/data/qa_dataset_test.json")
    print(f"加载了 {len(dataset)} 条问答数据")
    
    if not dataset:
        print("[错误] 数据集为空，实验终止")
        return
    
    # 步骤 3: 评估检索效果
    print("\n" + "=" * 80)
    print("步骤 3: 评估检索效果")
    print("=" * 80)
    
    results = evaluate_retrieval(
        dataset=dataset,
        chunker_types=chunker_types,
        embedder_type=embedder_type,
        top_k=top_k,
        request_delay=1.0  # 检索时的 API 延迟（固定为1秒）
    )
    
    # 步骤 4: 生成报告
    print("\n" + "=" * 80)
    print("步骤 4: 生成评估报告")
    print("=" * 80)
    
    generate_comparison_report(results, "experiment/data/evaluation_report_parent_child_test.txt")
    
    print("\n" + "=" * 80)
    print("实验完成！")
    print("=" * 80)
    print(f"\n结果保存在: experiment/data/")


def main():
    """主函数，支持命令行参数"""
    parser = argparse.ArgumentParser(description="Chunker 方法对比实验")
    
    parser.add_argument(
        '--num-fragments', 
        type=int, 
        default=1,
        help='文本片段数量（默认：5，实际实验可设为500）'
    )
    
    parser.add_argument(
        '--questions-per-fragment',
        type=int,
        default=5,
        help='每个片段生成的问题数量（默认：3）'
    )
    
    parser.add_argument(
        '--fragment-length',
        type=int,
        default=1000,
        help='文本片段长度（默认：1000）'
    )
    
    parser.add_argument(
        '--chunker-types',
        nargs='+',
        # default=['fixed', 'semantic', 'chapter'],
        default=['parent_child'],
        help='要评估的 chunker 类型（默认：fixed semantic chapter）'
    )
    
    parser.add_argument(
        '--embedder-type',
        type=str,
        default='local',
        help='Embedder 类型（默认：api）'
    )
    
    parser.add_argument(
        '--top-k',
        type=int,
        default=5,
        help='检索返回前 k 个结果（默认：5）'
    )
    
    parser.add_argument(
        '--request-delay',
        type=int,
        default=3,
        help='API 请求间隔（秒），避免限流（默认：3）'
    )
    
    args = parser.parse_args()
    
    run_full_experiment(
        num_fragments=args.num_fragments,
        questions_per_fragment=args.questions_per_fragment,
        fragment_length=args.fragment_length,
        chunker_types=args.chunker_types,
        embedder_type=args.embedder_type,
        top_k=args.top_k,
        request_delay=args.request_delay
    )


if __name__ == "__main__":
    main()
