"""重建知识库索引的脚本"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge import OfflineProcessor


def rebuild_index():
    """重建知识库索引"""
    print("="*60)
    print("重建知识库索引")
    print("="*60 + "\n")
    
    # 配置
    data_dir = "knowledge/data"
    output_dir = "knowledge/vector_store"
    
    # 创建处理器
    processor = OfflineProcessor(
        data_dir=data_dir,
        output_dir=output_dir,
        chunker_type="semantic",  # 语义分块，更符合自然段落
        chunk_size=500,
        chunk_overlap=50,
        embedder_type="simple"    # TF-IDF，不需要API
    )
    
    # 处理所有文档
    stats = processor.process_directory()
    
    # 输出统计
    print("\n" + "="*60)
    print("索引重建完成")
    print("="*60)
    print(f"处理文件: {stats['processed_files']}/{stats['total_files']}")
    print(f"失败文件: {stats['failed_files']}")
    print(f"总文本块: {stats['total_chunks']}")
    print("\n详细信息:")
    for detail in stats.get('files_details', []):
        print(f"  {detail['filename']}: {detail['chunks']} 块, {detail['chars']} 字符")


if __name__ == "__main__":
    rebuild_index()

