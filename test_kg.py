"""
测试 KGRetriever 知识图谱检索器
"""
import os
import sys
import traceback

# 保证可以以脚本方式直接运行
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from knowledge.retrievers.kg_retriever import KGRetriever


def safe_preview(text: str, max_len: int = 200) -> str:
    """
    为了避免 Windows 控制台 GBK 编码报错：
    - 截断文本长度
    - 去掉换行
    - 用 errors='ignore' 丢弃无法编码的字符
    """
    if not text:
        return ""
    s = text.replace("\n", " ").replace("\r", " ")
    if len(s) > max_len:
        s = s[:max_len] + "..."
    # 转成 GBK 可打印的子集，避免 UnicodeEncodeError
    s_safe = s.encode("gbk", errors="ignore").decode("gbk", errors="ignore")
    return s_safe


def test_kg_retriever():
    print("=" * 80)
    print("测试 KGRetriever - 知识图谱检索器")
    print("=" * 80)

    # 允许通过环境变量覆盖 Neo4j 配置
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "12345678")
    database = os.getenv("NEO4J_DATABASE", "papers")
    chunk_dir = os.getenv(
        "KG_CHUNK_DIR",
        "knowledge/chunkers/chunker_output/chapter",
    )
    embedder_type = os.getenv("KG_EMBEDDER_TYPE", "api")

    print("\n配置：")
    print(f"  Neo4j URI   : {neo4j_uri}")
    print(f"  Neo4j User  : {neo4j_user}")
    print(f"  Database    : {database}")
    print(f"  Chunk 目录  : {chunk_dir}")
    print(f"  Embedder    : {embedder_type}")

    print("\n" + "=" * 80)
    print("初始化 KGRetriever...")
    print("=" * 80)

    retriever = None
    try:
        retriever = KGRetriever(
            neo4j_uri=neo4j_uri,
            neo4j_user=neo4j_user,
            neo4j_password=neo4j_password,
            database=database,
            chunk_dir=chunk_dir,
            embedder_type=embedder_type,
        )
        print("\n[成功] KGRetriever 初始化完成")
    except Exception as e:
        print(f"\n[失败] 初始化 KGRetriever 失败: {e}")
        traceback.print_exc()
        return

    # 统计信息
    print("\n" + "=" * 80)
    print("知识图谱统计信息")
    print("=" * 80)
    try:
        stats = retriever.get_statistics()
        for k, v in stats.items():
            print(f"  {k}: {v}")
    except Exception as e:
        print(f"[警告] 获取统计信息失败: {e}")
        traceback.print_exc()

    # 测试查询
    print("\n" + "=" * 80)
    print("测试检索流程")
    print("=" * 80)

    test_queries = [
        "加速器束流诊断方法",
    ]

    for i, query in enumerate(test_queries, 1):
        print("\n" + "─" * 80)
        print(f"查询 {i}: {query}")
        print("─" * 80)

        try:
            # 1. 提取关键词
            keywords = retriever.extract_keywords(query)
            print(f"关键词: {keywords}")

            # 2. 从 KG 中检索相关 chunk 文件
            chunk_files = retriever.retrieve_related_chunks(query, max_neighbors=5)
            print(f"相关 chunk 数量: {len(chunk_files)}")
            preview_files = list(chunk_files)[:5]
            if preview_files:
                print("部分 chunk 文件示例:")
                for fname in preview_files:
                    print(f"  - {fname}")

            # 3. 读取并按相似度排序文档
            documents = retriever.retrieve_documents(
                query, max_neighbors=5, top_k=3
            )
            if not documents:
                print("未检索到相关文档内容")
                continue

            print("\n排序后的文档：")
            for j, doc in enumerate(documents, 1):
                preview = safe_preview(doc, max_len=220)
                print(f"\n  文档 {j}:")
                print(f"    {preview}")

        except Exception as e:
            print(f"[失败] 查询流程出错: {e}")
            traceback.print_exc()

    if retriever is not None:
        try:
            retriever.close()
        except Exception:
            pass

    print("\n" + "=" * 80)
    print("KG 检索测试结束")
    print("=" * 80)


if __name__ == "__main__":
    test_kg_retriever()

