"""离线文档处理器 - 解析、分块、向量化和索引"""
import os
import sys
from typing import List, Dict, Any, Optional

# 支持直接运行和作为模块导入
if __name__ == "__main__":
    # 直接运行时使用绝对导入
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from knowledge.parsers import ParserFactory
    from knowledge.chunkers import ChunkerFactory
    from knowledge.embeddings import create_embedder
    from knowledge.vector_store import FaissVectorStore
else:
    # 作为模块导入时使用相对导入
    from .parsers import ParserFactory
    from .chunkers import ChunkerFactory
    from .embeddings import create_embedder
    from .vector_store import FaissVectorStore


class OfflineProcessor:
    """离线文档处理器"""
    
    def __init__(
        self,
        data_dir: str,
        output_dir: str = "knowledge/vector_store",
        chunker_type: str = "semantic",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        embedder_type: str = "simple",
        **embedder_kwargs
    ):
        """
        初始化离线处理器
        
        Args:
            data_dir: 数据源目录
            output_dir: 输出目录（索引和文档）
            chunker_type: 分块器类型
            chunk_size: 块大小
            chunk_overlap: 块重叠
            embedder_type: 向量化方法
            **embedder_kwargs: 传递给embedder的参数
        """
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.chunker_type = chunker_type
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 初始化组件
        self.chunker = ChunkerFactory.create_chunker(
            chunker_type=chunker_type,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        self.embedder = create_embedder(embedder_type, **embedder_kwargs)
        self.vector_store = None
        
        print(f"离线处理器初始化完成")
        print(f"数据目录: {data_dir}")
        print(f"输出目录: {output_dir}")
        print(f"分块器: {chunker_type}")
        print(f"向量化: {embedder_type}")
    
    def process_directory(self, file_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        处理整个目录的文档
        
        Args:
            file_types: 要处理的文件类型列表，如 ['.pdf', '.txt']，None表示所有支持的类型
            
        Returns:
            处理统计信息
        """
        print(f"\n{'='*60}")
        print("开始离线文档处理")
        print(f"{'='*60}\n")
        
        # 扫描文件
        files_to_process = self._scan_directory(file_types)
        print(f"找到 {len(files_to_process)} 个文件待处理\n")
        
        if not files_to_process:
            print("没有找到可处理的文件")
            return {"error": "没有找到可处理的文件"}
        
        # 解析和分块
        all_chunks = []
        all_metadata = []
        stats = {
            "total_files": len(files_to_process),
            "processed_files": 0,
            "failed_files": 0,
            "total_chunks": 0,
            "files_details": []
        }
        
        for file_path in files_to_process:
            filename = os.path.basename(file_path)
            print(f"处理文件: {filename}")
            
            # 解析文档
            text = ParserFactory.parse_document(file_path)
            
            if not text:
                print(f"  跳过（解析失败或为空）\n")
                stats["failed_files"] += 1
                continue
            
            # 分块
            chunks = self.chunker.chunk(text)
            
            if not chunks:
                print(f"  跳过（分块失败）\n")
                stats["failed_files"] += 1
                continue
            
            # 保存块和元数据
            for chunk in chunks:
                all_chunks.append(chunk)
                all_metadata.append({
                    "source_file": filename,
                    "file_path": file_path,
                    "chunk_index": len(all_chunks) - 1
                })
            
            stats["processed_files"] += 1
            stats["files_details"].append({
                "filename": filename,
                "chunks": len(chunks),
                "chars": len(text)
            })
            
            print(f"  生成 {len(chunks)} 个文本块\n")
        
        stats["total_chunks"] = len(all_chunks)
        
        print(f"\n{'='*60}")
        print(f"文档解析和分块完成")
        print(f"  成功: {stats['processed_files']} 个文件")
        print(f"  失败: {stats['failed_files']} 个文件")
        print(f"  总块数: {stats['total_chunks']} 个")
        print(f"{'='*60}\n")
        
        if not all_chunks:
            return stats
        
        # 向量化
        print("开始向量化...")
        
        # 如果是SimpleEmbedder，需要先fit
        if hasattr(self.embedder, 'fit'):
            print("训练向量化器...")
            self.embedder.fit(all_chunks)
        
        embeddings = self.embedder.embed(all_chunks)
        print(f"向量化完成，shape: {embeddings.shape}\n")
        
        # 创建向量存储
        print("构建FAISS索引...")
        self.vector_store = FaissVectorStore(dimension=embeddings.shape[1])
        self.vector_store.add_documents(embeddings, all_chunks)
        
        # 保存索引
        index_path = os.path.join(self.output_dir, "faiss_index.bin")
        docs_path = os.path.join(self.output_dir, "documents.pkl")
        
        self.vector_store.save(index_path, docs_path)
        
        # 保存元数据
        metadata_path = os.path.join(self.output_dir, "metadata.pkl")
        import pickle
        with open(metadata_path, 'wb') as f:
            pickle.dump(all_metadata, f)
        print(f"元数据已保存到: {metadata_path}")
        
        print(f"\n{'='*60}")
        print("离线处理完成!")
        print(f"{'='*60}\n")
        
        return stats
    
    def _scan_directory(self, file_types: Optional[List[str]] = None) -> List[str]:
        """
        扫描目录获取文件列表
        
        Args:
            file_types: 文件类型列表
            
        Returns:
            文件路径列表
        """
        if file_types is None:
            file_types = ['.pdf', '.txt']
        
        files = []
        for filename in os.listdir(self.data_dir):
            file_path = os.path.join(self.data_dir, filename)
            
            if os.path.isfile(file_path):
                _, ext = os.path.splitext(filename)
                if ext.lower() in file_types:
                    files.append(file_path)
        
        return sorted(files)
    
    def process_single_file(self, file_path: str) -> Dict[str, Any]:
        """
        处理单个文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            处理结果
        """
        print(f"处理单个文件: {file_path}")
        
        # 解析
        text = ParserFactory.parse_document(file_path)
        if not text:
            return {"error": "解析失败"}
        
        # 分块
        chunks = self.chunker.chunk(text)
        if not chunks:
            return {"error": "分块失败"}
        
        return {
            "filename": os.path.basename(file_path),
            "chunks": len(chunks),
            "chars": len(text),
            "sample_chunks": chunks[:3]  # 返回前3个块作为样例
        }


def main():
    """主函数 - 运行离线处理"""
    import sys
    
    # 配置
    data_dir = "knowledge/data"
    output_dir = "knowledge/vector_store"
    
    # 从命令行参数获取配置（可选）
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    
    # 创建处理器
    processor = OfflineProcessor(
        data_dir=data_dir,
        output_dir=output_dir,
        chunker_type="semantic",  # 使用语义分块
        chunk_size=500,
        chunk_overlap=50,
        embedder_type="simple"  # 使用TF-IDF，不需要API
    )
    
    # 处理所有文档
    stats = processor.process_directory()
    
    # 打印统计信息
    print("\n处理统计:")
    print(f"  总文件数: {stats['total_files']}")
    print(f"  成功处理: {stats['processed_files']}")
    print(f"  失败: {stats['failed_files']}")
    print(f"  总文本块: {stats['total_chunks']}")
    
    if stats.get('files_details'):
        print("\n文件详情:")
        for detail in stats['files_details']:
            print(f"  - {detail['filename']}: {detail['chunks']} 块, {detail['chars']} 字符")


if __name__ == "__main__":
    main()

