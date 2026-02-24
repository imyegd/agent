"""
Chunker 方法检索效果评估

功能：
1. 加载问答数据集
2. 使用不同 chunker 方法的索引检索问题
3. 评估检索准确率（是否检索到标签 chunk）
4. 生成对比报告
"""
import os
import sys
import json
import time
import numpy as np
from typing import List, Dict, Tuple

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge.embeddings import create_embedder
from knowledge.vector_store.faiss_store import FaissVectorStore


def load_qa_dataset(dataset_file: str = "experiment/data/qa_dataset.json") -> List[Dict]:
    """
    加载问答数据集
    
    Args:
        dataset_file: 数据集文件路径
        
    Returns:
        数据集列表
    """
    if not os.path.exists(dataset_file):
        print(f"[错误] 数据集文件不存在: {dataset_file}")
        return []
    
    with open(dataset_file, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    return dataset


def retrieve_with_chunker(question: str,
                         vector_store: FaissVectorStore,
                         embedder,
                         top_k: int = 5,
                         max_retries: int = 3,
                         retry_delay: int = 5,
                         request_delay: float = 1.0) -> List[Tuple[str, float]]:
    """
    使用已加载的索引检索问题（带重试机制）
    
    Args:
        question: 问题文本
        vector_store: 已加载的向量库
        embedder: 已创建的向量化器
        top_k: 返回前 k 个结果
        max_retries: 最大重试次数
        retry_delay: 重试延迟（秒）
        request_delay: 成功请求后的延迟（秒）
        
    Returns:
        [(chunk_text, score), ...]
    """
    for attempt in range(max_retries):
        try:
            # 生成查询向量（可能触发API调用）
            query_embedding = embedder.embed([question])[0]
            
            # 成功生成向量后延迟
            if request_delay > 0:
                time.sleep(request_delay)
            
            # 检索
            results = vector_store.search(query_embedding, top_k=top_k)
            
            # 返回 (chunk_text, score) 列表
            return results
        
        except Exception as e:
            error_msg = str(e)
            
            # 检查是否是限流错误（429）
            if "429" in error_msg or "rate limit" in error_msg.lower():
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (attempt + 1)  # 指数退避
                    print(f"      [限流] 检索遇到限流，等待 {wait_time} 秒后重试 (尝试 {attempt + 1}/{max_retries})...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"[错误] 检索失败: 达到最大重试次数 - {e}")
                    return []
            else:
                # 其他错误，直接返回
                print(f"[错误] 检索失败: {e}")
                return []
    
    return []


def get_chunk_id_from_result(result_text: str, chunker_type: str) -> str:
    """
    从检索结果中提取 chunk_id
    
    由于我们的 chunk 文件命名格式是: {source_file}_chunk_{id}.txt
    可以通过匹配 chunk 内容来找到对应的文件
    
    这里简化处理，返回 chunk 文本的前100字符作为标识
    """
    return result_text[:100]


def match_chunk_file_by_content(chunk_text: str, 
                                chunker_type: str,
                                chunker_output_dir: str = "knowledge/chunkers/chunker_output") -> str:
    """
    根据 chunk 内容匹配对应的 chunk 文件名
    
    Args:
        chunk_text: chunk 文本内容
        chunker_type: chunker 类型
        chunker_output_dir: chunker 输出目录
        
    Returns:
        chunk 文件名
    """
    chunker_dir = os.path.join(chunker_output_dir, chunker_type)
    
    if not os.path.exists(chunker_dir):
        return ""
    
    # 遍历所有 chunk 文件，找到内容匹配的
    for chunk_file in os.listdir(chunker_dir):
        if not chunk_file.endswith('.txt'):
            continue
        
        chunk_path = os.path.join(chunker_dir, chunk_file)
        
        try:
            with open(chunk_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            # 如果内容完全匹配，返回文件名
            if file_content.strip() == chunk_text.strip():
                return chunk_file
        
        except Exception as e:
            continue
    
    return ""


def evaluate_retrieval(dataset: List[Dict],
                      chunker_types: List[str],
                      embedder_type: str = "api",
                      top_k: int = 5,
                      request_delay: float = 1.0) -> Dict:
    """
    评估不同 chunker 的检索效果
    
    Args:
        dataset: 问答数据集
        chunker_types: 要评估的 chunker 类型列表
        embedder_type: embedder 类型
        top_k: 检索返回前 k 个结果
        request_delay: API 请求延迟（秒），避免限流
        
    Returns:
        评估结果字典
    """
    print("=" * 80)
    print("检索效果评估")
    print("=" * 80)
    
    results = {}
    
    for chunker_type in chunker_types:
        print(f"\n[评估] Chunker: {chunker_type}")
        
        # 加载索引（每个 chunker 只加载一次）
        index_dir = f"knowledge/vector_store/index/{chunker_type}_{embedder_type}"
        
        if not os.path.exists(index_dir):
            print(f"  [警告] 索引目录不存在: {index_dir}")
            results[chunker_type] = {
                'total': 0,
                'correct_at_1': 0, 'correct_at_2': 0, 'correct_at_3': 0,
                'correct_at_4': 0, 'correct_at_5': 0,
                'accuracy_at_1': 0.0, 'accuracy_at_2': 0.0, 'accuracy_at_3': 0.0,
                'accuracy_at_4': 0.0, 'accuracy_at_5': 0.0,
                'mrr': 0.0
            }
            continue
        
        # 构建索引和文档路径
        index_file = os.path.join(index_dir, "faiss_index.bin")
        documents_file = os.path.join(index_dir, "documents.pkl")
        
        if not os.path.exists(index_file) or not os.path.exists(documents_file):
            print(f"  [警告] 索引文件不存在: {index_dir}")
            results[chunker_type] = {
                'total': 0,
                'correct_at_1': 0, 'correct_at_2': 0, 'correct_at_3': 0,
                'correct_at_4': 0, 'correct_at_5': 0,
                'accuracy_at_1': 0.0, 'accuracy_at_2': 0.0, 'accuracy_at_3': 0.0,
                'accuracy_at_4': 0.0, 'accuracy_at_5': 0.0,
                'mrr': 0.0
            }
            continue
        
        try:
            # 创建 embedder（每个 chunker 只创建一次）
            print(f"  创建向量化器...")
            embedder = create_embedder(method=embedder_type)
            
            # 加载向量库（每个 chunker 只加载一次）
            print(f"  加载索引...")
            vector_store = FaissVectorStore()
            vector_store.load(index_file, documents_file)
            print(f"  索引加载完成: {len(vector_store.documents)} 个文档")
            
            # 加载元数据（特别是对于 parent_child 类型）
            metadata_file = os.path.join(index_dir, "metadata.pkl")
            metadata_list = []
            if os.path.exists(metadata_file):
                import pickle
                with open(metadata_file, 'rb') as f:
                    metadata_list = pickle.load(f)
                print(f"  元数据加载完成: {len(metadata_list)} 条记录")
            
        except Exception as e:
            print(f"  [错误] 加载索引失败: {e}")
            results[chunker_type] = {
                'total': 0,
                'correct_at_1': 0, 'correct_at_2': 0, 'correct_at_3': 0,
                'correct_at_4': 0, 'correct_at_5': 0,
                'accuracy_at_1': 0.0, 'accuracy_at_2': 0.0, 'accuracy_at_3': 0.0,
                'accuracy_at_4': 0.0, 'accuracy_at_5': 0.0,
                'mrr': 0.0
            }
            continue
        
        # 评估指标
        correct_at = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}  # Top-1/2/3/4/5 准确数
        total = 0
        mrr_scores = []  # Mean Reciprocal Rank
        
        for i, item in enumerate(dataset, 1):
            question = item['question']
            label_chunk = item['chunk_labels'].get(chunker_type, {}).get('chunk_file', '')
            
            if not label_chunk:
                continue
            
            # 检索（使用已加载的索引和 embedder）
            search_results = retrieve_with_chunker(
                question,
                vector_store,
                embedder,
                top_k,
                request_delay=request_delay
            )
            
            if not search_results:
                continue
            
            # 匹配 chunk 文件
            retrieved_chunks = []
            for result_idx, (chunk_text, score) in enumerate(search_results):
                # 对于 parent_child 类型，从元数据中获取父块文件名
                if chunker_type == "parent_child" and metadata_list:
                    # 找到这个 chunk_text 在 documents 中的索引
                    try:
                        doc_idx = vector_store.documents.index(chunk_text)
                        if doc_idx < len(metadata_list):
                            meta = metadata_list[doc_idx]
                            # 使用父块文件名（与 chapter 分块的文件名格式一致）
                            parent_filename = meta.get('parent_filename', '')
                            if parent_filename:
                                retrieved_chunks.append(parent_filename)
                                continue
                    except ValueError:
                        pass
                
                # 其他类型或者没有元数据时，通过内容匹配
                chunk_file = match_chunk_file_by_content(chunk_text, chunker_type)
                if chunk_file:
                    retrieved_chunks.append(chunk_file)
            
            # 评估
            total += 1
            
            # 计算 Top-K 准确率 (K=1,2,3,4,5)
            for k in [1, 2, 3, 4, 5]:
                if label_chunk in retrieved_chunks[:k]:
                    correct_at[k] += 1
            
            # MRR: 1 / rank
            if label_chunk in retrieved_chunks:
                rank = retrieved_chunks.index(label_chunk) + 1
                mrr_scores.append(1.0 / rank)
            else:
                mrr_scores.append(0.0)
            
            if i % 50 == 0:
                print(f"  已评估: {i}/{len(dataset)} 个问题")
        
        # 计算指标
        if total > 0:
            accuracy_at = {k: correct_at[k] / total for k in [1, 2, 3, 4, 5]}
            mrr = np.mean(mrr_scores) if mrr_scores else 0.0
        else:
            accuracy_at = {k: 0.0 for k in [1, 2, 3, 4, 5]}
            mrr = 0.0
        
        results[chunker_type] = {
            'total': total,
            'correct_at_1': correct_at[1],
            'correct_at_2': correct_at[2],
            'correct_at_3': correct_at[3],
            'correct_at_4': correct_at[4],
            'correct_at_5': correct_at[5],
            'accuracy_at_1': accuracy_at[1],
            'accuracy_at_2': accuracy_at[2],
            'accuracy_at_3': accuracy_at[3],
            'accuracy_at_4': accuracy_at[4],
            'accuracy_at_5': accuracy_at[5],
            'mrr': mrr
        }
        
        print(f"\n  结果:")
        print(f"    总问题数: {total}")
        print(f"    Top-1 准确率: {accuracy_at[1]:.2%} ({correct_at[1]}/{total})")
        print(f"    Top-2 准确率: {accuracy_at[2]:.2%} ({correct_at[2]}/{total})")
        print(f"    Top-3 准确率: {accuracy_at[3]:.2%} ({correct_at[3]}/{total})")
        print(f"    Top-4 准确率: {accuracy_at[4]:.2%} ({correct_at[4]}/{total})")
        print(f"    Top-5 准确率: {accuracy_at[5]:.2%} ({correct_at[5]}/{total})")
        print(f"    MRR: {mrr:.4f}")
    
    return results


def generate_comparison_report(results: Dict, output_file: str = "experiment/data/evaluation_report.txt"):
    """
    生成对比报告
    
    Args:
        results: 评估结果
        output_file: 输出文件路径
    """
    print("\n" + "=" * 80)
    print("评估报告")
    print("=" * 80)
    
    # 控制台输出
    print(f"\n{'Chunker':<15} {'Top-1':<10} {'Top-2':<10} {'Top-3':<10} {'Top-4':<10} {'Top-5':<10} {'MRR':<10}")
    print("-" * 85)
    
    for chunker_type, result in results.items():
        print(f"{chunker_type:<15} "
              f"{result['accuracy_at_1']:<10.2%} "
              f"{result['accuracy_at_2']:<10.2%} "
              f"{result['accuracy_at_3']:<10.2%} "
              f"{result['accuracy_at_4']:<10.2%} "
              f"{result['accuracy_at_5']:<10.2%} "
              f"{result['mrr']:<10.4f}")
    
    # 找出最佳方法
    best_chunker_at_1 = max(results.items(), key=lambda x: x[1]['accuracy_at_1'])
    best_chunker_at_5 = max(results.items(), key=lambda x: x[1]['accuracy_at_5'])
    best_chunker_mrr = max(results.items(), key=lambda x: x[1]['mrr'])
    
    print(f"\n最佳方法:")
    print(f"  Top-1 准确率: {best_chunker_at_1[0]} ({best_chunker_at_1[1]['accuracy_at_1']:.2%})")
    print(f"  Top-5 准确率: {best_chunker_at_5[0]} ({best_chunker_at_5[1]['accuracy_at_5']:.2%})")
    print(f"  MRR: {best_chunker_mrr[0]} ({best_chunker_mrr[1]['mrr']:.4f})")
    
    # 保存到文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 85 + "\n")
        f.write("Chunker 方法检索效果评估报告\n")
        f.write("=" * 85 + "\n\n")
        
        f.write(f"{'Chunker':<15} {'Top-1':<10} {'Top-2':<10} {'Top-3':<10} {'Top-4':<10} {'Top-5':<10} {'MRR':<10}\n")
        f.write("-" * 85 + "\n")
        
        for chunker_type, result in results.items():
            f.write(f"{chunker_type:<15} "
                   f"{result['accuracy_at_1']:<10.2%} "
                   f"{result['accuracy_at_2']:<10.2%} "
                   f"{result['accuracy_at_3']:<10.2%} "
                   f"{result['accuracy_at_4']:<10.2%} "
                   f"{result['accuracy_at_5']:<10.2%} "
                   f"{result['mrr']:<10.4f}\n")
        
        f.write(f"\n最佳方法:\n")
        f.write(f"  Top-1 准确率: {best_chunker_at_1[0]} ({best_chunker_at_1[1]['accuracy_at_1']:.2%})\n")
        f.write(f"  Top-5 准确率: {best_chunker_at_5[0]} ({best_chunker_at_5[1]['accuracy_at_5']:.2%})\n")
        f.write(f"  MRR: {best_chunker_mrr[0]} ({best_chunker_mrr[1]['mrr']:.4f})\n")
        
        f.write("\n详细结果:\n")
        f.write("-" * 85 + "\n")
        
        for chunker_type, result in results.items():
            f.write(f"\n{chunker_type}:\n")
            f.write(f"  总问题数: {result['total']}\n")
            f.write(f"  Top-1 正确: {result['correct_at_1']} (准确率: {result['accuracy_at_1']:.2%})\n")
            f.write(f"  Top-2 正确: {result['correct_at_2']} (准确率: {result['accuracy_at_2']:.2%})\n")
            f.write(f"  Top-3 正确: {result['correct_at_3']} (准确率: {result['accuracy_at_3']:.2%})\n")
            f.write(f"  Top-4 正确: {result['correct_at_4']} (准确率: {result['accuracy_at_4']:.2%})\n")
            f.write(f"  Top-5 正确: {result['correct_at_5']} (准确率: {result['accuracy_at_5']:.2%})\n")
            f.write(f"  MRR: {result['mrr']:.4f}\n")
    
    print(f"\n报告已保存到: {output_file}")


def main():
    """主函数"""
    # 1. 加载数据集
    print("[步骤 1] 加载问答数据集...")
    dataset = load_qa_dataset("experiment/data/qa_dataset.json")
    print(f"  加载了 {len(dataset)} 条问答数据")
    
    if not dataset:
        print("[错误] 数据集为空，请先运行 generate_questions.py 生成数据")
        return
    
    # 2. 评估不同 chunker
    print("\n[步骤 2] 评估不同 chunker 的检索效果...")
    chunker_types = ["fixed", "semantic", "chapter"]
    
    results = evaluate_retrieval(
        dataset=dataset,
        chunker_types=chunker_types,
        embedder_type="api",
        top_k=5,
        request_delay=1.0  # 检索时的 API 延迟
    )
    
    # 3. 生成报告
    print("\n[步骤 3] 生成评估报告...")
    generate_comparison_report(results, "experiment/data/evaluation_report.txt")


if __name__ == "__main__":
    main()
