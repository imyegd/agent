"""
测试混合检索器（TF-IDF + Vector + RRF）
从 parent_child_api 索引加载
"""
from knowledge.retrievers.hybrid_retriever import HybridRetriever
from knowledge.vector_store.faiss_store import FaissVectorStore
import os
import pickle

# 配置路径
chunker_type = "parent_child"
embedder_type = "api"
index_dir = f"knowledge/vector_store/index/{chunker_type}_{embedder_type}"

print("=" * 80)
print("测试混合检索器（Hybrid Retriever）")
print("=" * 80)
print(f"\n使用索引: {index_dir}")

# 加载索引和文档
print("\n[1/3] 加载索引和文档...")
index_file = os.path.join(index_dir, "faiss_index.bin")
documents_file = os.path.join(index_dir, "documents.pkl")

vector_store = FaissVectorStore()
vector_store.load(index_file, documents_file)
documents = vector_store.documents
print(f"  ✓ 索引加载完成: {len(documents)} 个文档")

# 加载元数据
metadata_file = os.path.join(index_dir, "metadata.pkl")
metadata_list = []
if os.path.exists(metadata_file):
    with open(metadata_file, 'rb') as f:
        metadata_list = pickle.load(f)
    print(f"  ✓ 元数据加载完成: {len(metadata_list)} 条记录")
    
    # 统计父子关系
    with_parent = sum(1 for m in metadata_list if 'parent_chunk' in m)
    print(f"  ✓ 包含父块信息的子块: {with_parent} 个")

# 初始化混合检索器
print("\n[2/3] 初始化混合检索器...")
hybrid_retriever = HybridRetriever(
    documents=documents,
    embedder_type=embedder_type,
    rrf_k=60,  # RRF 平滑常数
    index_path=index_dir  # 传递索引路径，避免重新构建
)

# 显示统计信息
print("\n[3/3] 检索器统计信息:")
stats = hybrid_retriever.get_statistics()
print(f"  - 检索器类型: {stats['retriever_type']}")
print(f"  - 向量类型: {stats['embedder_type']}")
print(f"  - 文档数量: {stats['document_count']}")
print(f"  - 向量维度: {stats['embedding_dimension']}")
print(f"  - 词汇表大小: {stats['vocabulary_size']}")
print(f"  - TF-IDF 矩阵: {stats['tfidf_matrix_shape']}")
print(f"  - RRF 参数 k: {stats['rrf_k']}")

# 测试查询
print("\n" + "=" * 80)
print("开始测试检索")
print("=" * 80)

test_queries = [
    "加速器束流如何调试？",
    "BEPCII 的主要特点是什么？",
    "重离子加速器的应用有哪些？"
]

for i, query in enumerate(test_queries, 1):
    print(f"\n查询 {i}: {query}")
    print("-" * 80)
    
    # 执行检索
    results = hybrid_retriever.retrieve(query, top_k=5)
    
    # 显示结果
    for j, (doc, score) in enumerate(results, 1):
        # 获取文档预览
        preview = doc[:200].replace('\n', ' ').replace('\r', '')
        if len(doc) > 200:
            preview += "..."
        
        print(f"\n  [{j}] RRF 分数: {score:.6f}")
        print(f"      {preview}")
        
        # 如果有元数据，显示额外信息
        if j - 1 < len(metadata_list):
            meta = metadata_list[results[j-1][0] if isinstance(results[j-1][0], int) else j-1]
            if 'filename' in meta:
                print(f"      文件: {meta['filename']}")
            if 'parent_filename' in meta and meta['parent_filename']:
                print(f"      父块: {meta['parent_filename']}")

print("\n" + "=" * 80)
print("测试完成！")
print("=" * 80)

print("\n说明：")
print("  - 混合检索 = TF-IDF 检索 + 向量检索 + RRF 融合")
print("  - TF-IDF: 基于关键词匹配，精确但缺乏语义理解")
print("  - Vector: 基于语义相似度，理解上下文但可能不够精确")
print("  - RRF: Reciprocal Rank Fusion，综合两种排名的优势")
print("  - 适合需要同时兼顾关键词和语义的场景")
