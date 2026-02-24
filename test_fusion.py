"""
测试 FusionRetriever 融合检索器
"""
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from knowledge.retrievers.fusion_retriever import FusionRetriever


def safe_preview(text: str, max_len: int = 220) -> str:
    """避免 Windows 控制台 GBK 编码报错的安全预览。"""
    if not text:
        return ""
    s = text.replace("\n", " ").replace("\r", " ")
    if len(s) > max_len:
        s = s[:max_len] + "..."
    return s.encode("gbk", errors="ignore").decode("gbk", errors="ignore")


def test_fusion():
    print("=" * 80)
    print("测试 FusionRetriever - 融合检索器")
    print("=" * 80)

    # 向量索引（用于 HybridRetriever）
    index_path = os.getenv(
        "FUSION_INDEX_PATH",
        "knowledge/vector_store/index/parent_child_api",
    )

    # KG 配置（用于 KGRetriever）
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "12345678")
    neo4j_database = os.getenv("NEO4J_DATABASE", "papers")
    chunk_dir = os.getenv(
        "KG_CHUNK_DIR",
        "knowledge/chunkers/chunker_output/chapter",
    )
    embedder_type = os.getenv("FUSION_EMBEDDER_TYPE", "api")

    print("\n配置：")
    print(f"  Index Path : {index_path}")
    print(f"  Neo4j URI  : {neo4j_uri}")
    print(f"  Neo4j User : {neo4j_user}")
    print(f"  Database   : {neo4j_database}")
    print(f"  Chunk 目录 : {chunk_dir}")
    print(f"  Embedder   : {embedder_type}")

    print("\n" + "=" * 80)
    print("初始化 FusionRetriever...")
    print("=" * 80)

    retriever = None
    try:
        retriever = FusionRetriever(
            index_path=index_path,
            embedder_type=embedder_type,
            neo4j_uri=neo4j_uri,
            neo4j_user=neo4j_user,
            neo4j_password=neo4j_password,
            neo4j_database=neo4j_database,
            chunk_dir=chunk_dir,
        )
        print("\n[成功] FusionRetriever 初始化完成")
    except Exception as e:
        print(f"\n[失败] 初始化 FusionRetriever 失败: {e}")
        traceback.print_exc()
        return

    # 不强制获取统计信息，避免 Neo4j 认证失败直接中断

    print("\n" + "=" * 80)
    print("测试融合检索")
    print("=" * 80)

    test_queries = [

        "加速器束流诊断方法",
        "知识图谱在论文检索中的作用",
    ]

    for i, query in enumerate(test_queries, 1):
        print("\n" + "─" * 80)
        print(f"查询 {i}: {query}")
        print("─" * 80)

        try:
            results = retriever.retrieve(
                query=query,
                top_k=3,
                hybrid_k=8,
                kg_k=5,
                use_kg=True,
            )

            if not results:
                print("未检索到相关文档")
                continue

            print(f"融合后返回 {len(results)} 个文档：")
            for j, (doc, score) in enumerate(results, 1):
                preview = safe_preview(doc)
                print(f"\n  文档 {j}  (score={score:.4f}):")
                print(f"    {preview}")

        except Exception as e:
            print(f"[失败] 融合检索流程出错: {e}")
            traceback.print_exc()

    if retriever is not None:
        try:
            retriever.close()
        except Exception:
            pass

    print("\n" + "=" * 80)
    print("Fusion 检索测试结束")
    print("=" * 80)


if __name__ == "__main__":
    test_fusion()

