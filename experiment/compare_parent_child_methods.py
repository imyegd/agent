"""
对比 parent_child 分块下不同检索方法的准确率

测试三种检索方法：
1. Keyword 检索（TF-IDF 关键词匹配）
2. Vector 检索（使用预加载的 FAISS 索引）
3. Hybrid 检索（RRF 融合 Keyword + Vector）

固定使用 parent_child_local 索引（预计算的 Qwen3-Embedding-0.6B 向量）
所有方法都优化为使用预构建索引，无需重新 embed 文档
"""
import os
import sys
import json
import pickle
import numpy as np
from typing import List, Dict, Tuple

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge.embeddings import create_embedder
from knowledge.vector_store.faiss_store import FaissVectorStore
from knowledge.retrievers import KeywordRetriever, VectorRetriever, HybridRetriever
from config.config import Config


def load_qa_dataset(dataset_file: str) -> List[Dict]:
    """加载问答数据集"""
    if not os.path.exists(dataset_file):
        print(f"[错误] 数据集文件不存在: {dataset_file}")
        return []
    
    with open(dataset_file, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    return dataset


def load_parent_child_index():
    """
    加载 parent_child_local 索引和文档
        
    Returns:
        (documents, metadata_list, vector_store)
    """
    index_dir = "knowledge/vector_store/index/parent_child_local"
    
    if not os.path.exists(index_dir):
        raise FileNotFoundError(
            f"索引目录不存在: {index_dir}\n"
            f"请先构建索引:\n"
            f"  python knowledge/chunkers/chunker_factory.py --chunker-type parent_child\n"
            f"  python knowledge/vector_store/faiss_store.py --chunker-type parent_child --embedder-type local"
        )
    
    index_file = os.path.join(index_dir, "faiss_index.bin")
    documents_file = os.path.join(index_dir, "documents.pkl")
    metadata_file = os.path.join(index_dir, "metadata.pkl")
    
    # 加载向量库
    print(f"  加载索引: {index_dir}")
    vector_store = FaissVectorStore()
    vector_store.load(index_file, documents_file)
    print(f"  索引加载完成: {len(vector_store.documents)} 个文档")
    
    # 加载元数据
    metadata_list = []
    if os.path.exists(metadata_file):
        with open(metadata_file, 'rb') as f:
            metadata_list = pickle.load(f)
        print(f"  元数据加载完成: {len(metadata_list)} 条记录")
    
    return vector_store.documents, metadata_list, vector_store


def rrf_fusion(
    keyword_results: List[Tuple[str, float]],
    vector_results: List[Tuple[str, float]],
    k: int = 60,
    top_k: int = 5
) -> List[Tuple[str, float]]:
    """
    RRF (Reciprocal Rank Fusion) 融合两个排名列表
    
    公式: Score(d) = Σ 1/(k + rank(d))
    
    Args:
        keyword_results: 关键词检索结果 [(doc, score), ...]
        vector_results: 向量检索结果 [(doc, score), ...]
        k: RRF 平滑常数（默认 60）
        top_k: 返回结果数
        
    Returns:
        融合后的结果列表 [(doc, rrf_score), ...]
    """
    # 构建排名字典
    keyword_ranks = {doc: rank + 1 for rank, (doc, _) in enumerate(keyword_results)}
    vector_ranks = {doc: rank + 1 for rank, (doc, _) in enumerate(vector_results)}
    
    # 获取所有文档
    all_docs = set(keyword_ranks.keys()) | set(vector_ranks.keys())
    
    # 计算 RRF 分数
    rrf_scores = {}
    for doc in all_docs:
        score = 0.0
        if doc in keyword_ranks:
            score += 1.0 / (k + keyword_ranks[doc])
        if doc in vector_ranks:
            score += 1.0 / (k + vector_ranks[doc])
        rrf_scores[doc] = score
    
    # 按 RRF 分数排序
    sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    
    return sorted_docs


def evaluate_retrieval_method(
    dataset: List[Dict],
    retriever,
    method_name: str,
    metadata_list: List[Dict],
    documents: List[str],
    top_k: int = 5
) -> Dict:
    """
    评估指定检索方法的效果
    
    Args:
        dataset: 问答数据集
        retriever: 检索器实例（KeywordRetriever, VectorRetriever, HybridRetriever）
        method_name: 方法名称
        metadata_list: 元数据列表
        documents: 文档列表
        top_k: 返回前 k 个结果
        
    Returns:
        评估结果字典
    """
    import time
    
    print(f"\n{'='*80}")
    print(f"评估: {method_name}")
    print(f"{'='*80}")
    print(f"  总问题数: {len(dataset)}")
    
    correct_at = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    total = 0
    mrr_scores = []
    
    start_time = time.time()
    
    for i, item in enumerate(dataset, 1):
        question = item['question']
        label_chunk = item['chunk_labels'].get('parent_child', {}).get('chunk_file', '')
        
        if not label_chunk:
            continue
        
        try:
            # 检索
            search_results = retriever.retrieve(question, top_k=top_k)
            
            if not search_results:
                continue
            
            # 匹配 chunk 文件（使用元数据中的 parent_filename）
            retrieved_chunks = []
            for chunk_text, score in search_results:
                # 找到这个 chunk_text 在 documents 中的索引
                try:
                    doc_idx = documents.index(chunk_text)
                    if doc_idx < len(metadata_list):
                        meta = metadata_list[doc_idx]
                        parent_filename = meta.get('parent_filename', '')
                        if parent_filename:
                            retrieved_chunks.append(parent_filename)
                except ValueError:
                    pass
            
            # 评估
            total += 1
            
            # Top-K 准确率
            for k in [1, 2, 3, 4, 5]:
                if label_chunk in retrieved_chunks[:k]:
                    correct_at[k] += 1
            
            # MRR
            if label_chunk in retrieved_chunks:
                rank = retrieved_chunks.index(label_chunk) + 1
                mrr_scores.append(1.0 / rank)
            else:
                mrr_scores.append(0.0)
            
            # 显示进度（每10个问题或每10%）
            if i % 10 == 0 or i % (len(dataset) // 10) == 0:
                elapsed = time.time() - start_time
                avg_time = elapsed / i
                remaining = avg_time * (len(dataset) - i)
                progress = (i / len(dataset)) * 100
                print(f"  进度: {i}/{len(dataset)} ({progress:.1f}%) | "
                      f"已用时: {elapsed:.1f}s | 预计剩余: {remaining:.1f}s")
        
        except Exception as e:
            print(f"  [警告] 问题 {i} 检索失败: {e}")
            continue
    
    # 计算指标
    if total > 0:
        accuracy_at = {k: correct_at[k] / total for k in [1, 2, 3, 4, 5]}
        mrr = np.mean(mrr_scores) if mrr_scores else 0.0
    else:
        accuracy_at = {k: 0.0 for k in [1, 2, 3, 4, 5]}
        mrr = 0.0
    
    results = {
        'method_name': method_name,
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


def generate_comparison_report(
    results: Dict, 
    output_file: str = "experiment/data/parent_child_methods_comparison.txt",
    eval_time: float = 0.0
):
    """生成检索方法对比报告"""
    print("\n" + "=" * 90)
    print("Parent-Child 分块 - 检索方法对比报告")
    print("=" * 90)
    if eval_time > 0:
        print(f"评估总耗时: {eval_time:.1f} 秒 ({eval_time/60:.1f} 分钟)\n")
    
    # 控制台输出
    print(f"\n{'Method':<25} {'Top-1':<10} {'Top-2':<10} {'Top-3':<10} {'Top-4':<10} {'Top-5':<10} {'MRR':<10}")
    print("-" * 95)
    
    for method_name, result in results.items():
        print(f"{method_name:<25} "
              f"{result['accuracy_at_1']:<10.2%} "
              f"{result['accuracy_at_2']:<10.2%} "
              f"{result['accuracy_at_3']:<10.2%} "
              f"{result['accuracy_at_4']:<10.2%} "
              f"{result['accuracy_at_5']:<10.2%} "
              f"{result['mrr']:<10.4f}")
    
    # 找到最佳方法
    best_at_1 = max(results.items(), key=lambda x: x[1]['accuracy_at_1'])
    best_at_5 = max(results.items(), key=lambda x: x[1]['accuracy_at_5'])
    best_mrr = max(results.items(), key=lambda x: x[1]['mrr'])
    
    print(f"\n最佳方法:")
    print(f"  Top-1 准确率: {best_at_1[0]} ({best_at_1[1]['accuracy_at_1']:.2%})")
    print(f"  Top-5 准确率: {best_at_5[0]} ({best_at_5[1]['accuracy_at_5']:.2%})")
    print(f"  MRR: {best_mrr[0]} ({best_mrr[1]['mrr']:.4f})")
    
    # 保存到文件
    os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 95 + "\n")
        f.write("Parent-Child 分块 - 检索方法对比报告\n")
        f.write("=" * 95 + "\n\n")
        
        if eval_time > 0:
            f.write(f"评估总耗时: {eval_time:.1f} 秒 ({eval_time/60:.1f} 分钟)\n\n")
        
        f.write("实验设置:\n")
        f.write("  分块策略: parent_child (章节父块 + 固定大小子块)\n")
        f.write("  向量模型: local (Qwen3-Embedding-0.6B)\n")
        f.write("  检索方法:\n")
        f.write("    1. Keyword 检索 - TF-IDF 关键词匹配（max_features=5000）\n")
        f.write("    2. Vector 检索 - 使用预加载的 FAISS 索引（预计算向量）\n")
        f.write("    3. Hybrid 检索 - RRF 融合 Keyword + Vector（k=60）\n\n")
        f.write("优化说明:\n")
        f.write("  - Keyword 检索：每次运行重新构建 TF-IDF 索引\n")
        f.write("  - Vector 检索：直接使用预构建的 FAISS 索引，无需重新 embed，速度极快\n")
        f.write("  - Hybrid 检索：融合 Keyword 和 Vector 结果，兼顾精确性和语义理解\n\n")
        
        f.write("=" * 95 + "\n")
        f.write(f"{'Method':<25} {'Top-1':<10} {'Top-2':<10} {'Top-3':<10} {'Top-4':<10} {'Top-5':<10} {'MRR':<10}\n")
        f.write("-" * 95 + "\n")
        
        for method_name, result in results.items():
            f.write(f"{method_name:<25} "
                   f"{result['accuracy_at_1']:<10.2%} "
                   f"{result['accuracy_at_2']:<10.2%} "
                   f"{result['accuracy_at_3']:<10.2%} "
                   f"{result['accuracy_at_4']:<10.2%} "
                   f"{result['accuracy_at_5']:<10.2%} "
                   f"{result['mrr']:<10.4f}\n")
        
        f.write(f"\n最佳方法:\n")
        f.write(f"  Top-1 准确率: {best_at_1[0]} ({best_at_1[1]['accuracy_at_1']:.2%})\n")
        f.write(f"  Top-5 准确率: {best_at_5[0]} ({best_at_5[1]['accuracy_at_5']:.2%})\n")
        f.write(f"  MRR: {best_mrr[0]} ({best_mrr[1]['mrr']:.4f})\n")
        
        f.write(f"\n详细结果:\n")
        f.write("-" * 95 + "\n\n")
        
        for method_name, result in results.items():
            f.write(f"{method_name}:\n")
            f.write(f"  总问题数: {result['total']}\n")
            f.write(f"  Top-1 正确: {result['correct_at_1']} (准确率: {result['accuracy_at_1']:.2%})\n")
            f.write(f"  Top-2 正确: {result['correct_at_2']} (准确率: {result['accuracy_at_2']:.2%})\n")
            f.write(f"  Top-3 正确: {result['correct_at_3']} (准确率: {result['accuracy_at_3']:.2%})\n")
            f.write(f"  Top-4 正确: {result['correct_at_4']} (准确率: {result['accuracy_at_4']:.2%})\n")
            f.write(f"  Top-5 正确: {result['correct_at_5']} (准确率: {result['accuracy_at_5']:.2%})\n")
            f.write(f"  MRR: {result['mrr']:.4f}\n\n")
    
    print(f"\n报告已保存: {output_file}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="对比 parent_child 分块的三种检索方法（固定使用 local embedder）"
    )
    parser.add_argument('--dataset', type=str, 
                       default='experiment/data/qa_dataset.json',
                       help='数据集文件路径')
    parser.add_argument('--top-k', type=int, default=5,
                       help='检索返回前 k 个结果')
    
    args = parser.parse_args()
    
    print("=" * 90)
    print("Parent-Child 分块 - 检索方法对比实验")
    print("=" * 90)
    print(f"\n实验配置:")
    print(f"  分块策略: parent_child (章节父块 + 固定子块)")
    print(f"  向量模型: local (Qwen3-Embedding-0.6B)")
    print(f"  检索方法: Keyword vs Vector vs Hybrid")
    print(f"  数据集: {args.dataset}")
    print(f"  Top-K: {args.top_k}")
    print(f"\n优化说明:")
    print(f"  - Vector 检索直接使用预加载的 FAISS 索引")
    print(f"  - Hybrid 检索使用 RRF 融合 Keyword + Vector")
    print(f"  - 无需重新 embed 文档，检索速度极快")
    
    # 1. 加载数据集
    print(f"\n{'='*90}")
    print("步骤 1: 加载数据集")
    print(f"{'='*90}")
    
    dataset = load_qa_dataset(args.dataset)
    print(f"加载了 {len(dataset)} 条问答数据")
    
    if not dataset:
        print("[错误] 数据集为空，实验终止")
        return
    
    # 2. 加载索引
    print(f"\n{'='*90}")
    print("步骤 2: 加载 parent_child_local 索引")
    print(f"{'='*90}")
    
    try:
        documents, metadata_list, vector_store = load_parent_child_index()
    except Exception as e:
        print(f"[错误] 加载索引失败: {e}")
        return
    
    # 3. 准备检索器
    print(f"\n{'='*90}")
    print("步骤 3: 准备检索器")
    print(f"{'='*90}")
    
    # 方法 1: Keyword 检索器（TF-IDF 关键词匹配）
    print("  [1/3] 创建 Keyword 检索器 (TF-IDF 关键词匹配)...")
    keyword_retriever = KeywordRetriever(
        documents=documents,
        max_features=5000,
        ngram_range=(1, 2)
    )
    
    # 方法 2: Vector 检索器（直接使用已加载的 FAISS 索引）
    print("  [2/3] 准备 Vector 检索器 (使用已加载的 FAISS 索引)...")
    print("        无需重新构建，直接使用预计算的向量")
    # vector_store 已经加载了预计算的向量，直接用它检索
    # 创建 embedder 用于查询向量化
    from knowledge.embeddings import create_embedder
    query_embedder = create_embedder(method="local", **Config.get_local_embedding_config())
    
    # 方法 3: Hybrid 检索器（RRF 融合）
    print("  [3/3] 准备 Hybrid 检索器 (RRF 融合 Keyword + Vector)...")
    print("        使用已创建的 Keyword 检索器和 Vector 索引")
    
    print("  检索器准备完成")
    
    # 4. 评估三种方法
    print(f"\n{'='*90}")
    print("步骤 4: 评估检索方法")
    print(f"{'='*90}")
    
    import time
    total_eval_start_time = time.time()
    
    results = {}
    
    # 方法 1: Keyword 检索
    results['Keyword (TF-IDF)'] = evaluate_retrieval_method(
        dataset=dataset,
        retriever=keyword_retriever,
        method_name='Keyword (TF-IDF)',
        metadata_list=metadata_list,
        documents=documents,
        top_k=args.top_k
    )
    
    # 方法 2: Vector 检索（使用 FAISS 索引）
    print(f"\n{'='*80}")
    print(f"评估: Vector (local)")
    print(f"{'='*80}")
    print(f"  总问题数: {len(dataset)}")
    
    import time
    correct_at = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    total = 0
    mrr_scores = []
    
    start_time_vector = time.time()
    
    for i, item in enumerate(dataset, 1):
        question = item['question']
        label_chunk = item['chunk_labels'].get('parent_child', {}).get('chunk_file', '')
        
        if not label_chunk:
            continue
        
        try:
            # 用 query_embedder 向量化查询
            query_vec = query_embedder.embed([question])[0]
            
            # 直接用 vector_store 检索（使用预计算的向量）
            search_results = vector_store.search(query_vec, top_k=args.top_k)
            
            if not search_results:
                continue
            
            # 匹配 chunk 文件
            retrieved_chunks = []
            for chunk_text, score in search_results:
                try:
                    doc_idx = documents.index(chunk_text)
                    if doc_idx < len(metadata_list):
                        meta = metadata_list[doc_idx]
                        parent_filename = meta.get('parent_filename', '')
                        if parent_filename:
                            retrieved_chunks.append(parent_filename)
                except ValueError:
                    pass
            
            # 评估
            total += 1
            
            # Top-K 准确率
            for k in [1, 2, 3, 4, 5]:
                if label_chunk in retrieved_chunks[:k]:
                    correct_at[k] += 1
            
            # MRR
            if label_chunk in retrieved_chunks:
                rank = retrieved_chunks.index(label_chunk) + 1
                mrr_scores.append(1.0 / rank)
            else:
                mrr_scores.append(0.0)
            
            # 显示进度（每10个问题或每10%）
            if i % 10 == 0 or i % (len(dataset) // 10) == 0:
                elapsed = time.time() - start_time_vector
                avg_time = elapsed / i
                remaining = avg_time * (len(dataset) - i)
                progress = (i / len(dataset)) * 100
                print(f"  进度: {i}/{len(dataset)} ({progress:.1f}%) | "
                      f"已用时: {elapsed:.1f}s | 预计剩余: {remaining:.1f}s")
        
        except Exception as e:
            print(f"  [警告] 问题 {i} 检索失败: {e}")
            continue
    
    # 计算指标
    if total > 0:
        accuracy_at = {k: correct_at[k] / total for k in [1, 2, 3, 4, 5]}
        mrr = np.mean(mrr_scores) if mrr_scores else 0.0
    else:
        accuracy_at = {k: 0.0 for k in [1, 2, 3, 4, 5]}
        mrr = 0.0
    
    results['Vector (local)'] = {
        'method_name': 'Vector (local)',
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
    
    # 方法 3: Hybrid 检索（RRF 融合）
    print(f"\n{'='*80}")
    print(f"评估: Hybrid (local)")
    print(f"{'='*80}")
    print(f"  总问题数: {len(dataset)}")
    
    correct_at_hybrid = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    total_hybrid = 0
    mrr_scores_hybrid = []
    
    start_time_hybrid = time.time()
    
    for i, item in enumerate(dataset, 1):
        question = item['question']
        label_chunk = item['chunk_labels'].get('parent_child', {}).get('chunk_file', '')
        
        if not label_chunk:
            continue
        
        try:
            # 1. Keyword 检索
            keyword_results = keyword_retriever.retrieve(question, top_k=args.top_k * 2)
            
            # 2. Vector 检索
            query_vec = query_embedder.embed([question])[0]
            vector_results = vector_store.search(query_vec, top_k=args.top_k * 2)
            
            # 3. RRF 融合
            hybrid_results = rrf_fusion(keyword_results, vector_results, k=60, top_k=args.top_k)
            
            if not hybrid_results:
                continue
            
            # 匹配 chunk 文件
            retrieved_chunks = []
            for chunk_text, score in hybrid_results:
                try:
                    doc_idx = documents.index(chunk_text)
                    if doc_idx < len(metadata_list):
                        meta = metadata_list[doc_idx]
                        parent_filename = meta.get('parent_filename', '')
                        if parent_filename:
                            retrieved_chunks.append(parent_filename)
                except ValueError:
                    pass
            
            # 评估
            total_hybrid += 1
            
            # Top-K 准确率
            for k in [1, 2, 3, 4, 5]:
                if label_chunk in retrieved_chunks[:k]:
                    correct_at_hybrid[k] += 1
            
            # MRR
            if label_chunk in retrieved_chunks:
                rank = retrieved_chunks.index(label_chunk) + 1
                mrr_scores_hybrid.append(1.0 / rank)
            else:
                mrr_scores_hybrid.append(0.0)
            
            # 显示进度（每10个问题或每10%）
            if i % 10 == 0 or i % (len(dataset) // 10) == 0:
                elapsed = time.time() - start_time_hybrid
                avg_time = elapsed / i
                remaining = avg_time * (len(dataset) - i)
                progress = (i / len(dataset)) * 100
                print(f"  进度: {i}/{len(dataset)} ({progress:.1f}%) | "
                      f"已用时: {elapsed:.1f}s | 预计剩余: {remaining:.1f}s")
        
        except Exception as e:
            print(f"  [警告] 问题 {i} 检索失败: {e}")
            continue
    
    # 计算指标
    if total_hybrid > 0:
        accuracy_at_hybrid = {k: correct_at_hybrid[k] / total_hybrid for k in [1, 2, 3, 4, 5]}
        mrr_hybrid = np.mean(mrr_scores_hybrid) if mrr_scores_hybrid else 0.0
    else:
        accuracy_at_hybrid = {k: 0.0 for k in [1, 2, 3, 4, 5]}
        mrr_hybrid = 0.0
    
    results['Hybrid (local)'] = {
        'method_name': 'Hybrid (local)',
        'total': total_hybrid,
        'correct_at_1': correct_at_hybrid[1],
        'correct_at_2': correct_at_hybrid[2],
        'correct_at_3': correct_at_hybrid[3],
        'correct_at_4': correct_at_hybrid[4],
        'correct_at_5': correct_at_hybrid[5],
        'accuracy_at_1': accuracy_at_hybrid[1],
        'accuracy_at_2': accuracy_at_hybrid[2],
        'accuracy_at_3': accuracy_at_hybrid[3],
        'accuracy_at_4': accuracy_at_hybrid[4],
        'accuracy_at_5': accuracy_at_hybrid[5],
        'mrr': mrr_hybrid
    }
    
    print(f"\n  结果:")
    print(f"    总问题数: {total_hybrid}")
    print(f"    Top-1 准确率: {accuracy_at_hybrid[1]:.2%} ({correct_at_hybrid[1]}/{total_hybrid})")
    print(f"    Top-2 准确率: {accuracy_at_hybrid[2]:.2%} ({correct_at_hybrid[2]}/{total_hybrid})")
    print(f"    Top-3 准确率: {accuracy_at_hybrid[3]:.2%} ({correct_at_hybrid[3]}/{total_hybrid})")
    print(f"    Top-4 准确率: {accuracy_at_hybrid[4]:.2%} ({correct_at_hybrid[4]}/{total_hybrid})")
    print(f"    Top-5 准确率: {accuracy_at_hybrid[5]:.2%} ({correct_at_hybrid[5]}/{total_hybrid})")
    print(f"    MRR: {mrr_hybrid:.4f}")
    
    # 评估总结
    total_eval_time = time.time() - total_eval_start_time
    print(f"\n{'='*90}")
    print(f"评估完成！总耗时: {total_eval_time:.1f} 秒 ({total_eval_time/60:.1f} 分钟)")
    print(f"{'='*90}")
    
    # 5. 生成报告
    print(f"\n{'='*90}")
    print("步骤 5: 生成对比报告")
    print(f"{'='*90}")
    
    generate_comparison_report(results, eval_time=total_eval_time)
    
    print("\n" + "=" * 90)
    print("实验完成！")
    print("=" * 90)
    print("\n说明:")
    print("  - Keyword 检索：使用 TF-IDF 重新构建索引（每次运行都构建）")
    print("  - Vector 检索：直接使用预加载的 FAISS 索引（无需重新 embed）")
    print("  - Hybrid 检索：RRF 融合 Keyword + Vector 结果（k=60）")


if __name__ == "__main__":
    main()
