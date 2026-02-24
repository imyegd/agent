"""分块器工厂"""
from typing import Dict, Any

import os
import sys
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from knowledge.chunkers.base_chunker import BaseChunker
    from knowledge.chunkers.fixed_size_chunker import FixedSizeChunker
    from knowledge.chunkers.semantic_chunker import SemanticChunker
    from knowledge.chunkers.chapter_chunker import ChapterChunker
    from knowledge.chunkers.parent_child_chunker import ParentChildChunker
else:
    from .base_chunker import BaseChunker
    from .fixed_size_chunker import FixedSizeChunker
    from .semantic_chunker import SemanticChunker
    from .chapter_chunker import ChapterChunker
    from .parent_child_chunker import ParentChildChunker

class ChunkerFactory:
    """分块器工厂类"""
    
    @staticmethod
    def create_chunker(chunker_type: str = "fixed", **kwargs) -> BaseChunker:
        """
        创建指定类型的分块器
        
        Args:
            chunker_type: 分块器类型，可选 "fixed", "semantic", "chapter", "parent_child"
            **kwargs: 传递给分块器的参数
            
            对于 parent_child 类型，需要提供：
                - parent_type: 父块类型 ("chapter", "semantic", "fixed")
                - child_type: 子块类型 ("fixed", "semantic")
                - parent_kwargs: 父块分块器参数
                - child_kwargs: 子块分块器参数
            
        Returns:
            分块器实例
        """
        if chunker_type == "fixed":
            return FixedSizeChunker(
                chunk_size=kwargs.get('chunk_size', 500),
                chunk_overlap=kwargs.get('chunk_overlap', 50)
            )
        elif chunker_type == "semantic":
            return SemanticChunker(
                embedder=kwargs.get('embedder', None),
                similarity_threshold=kwargs.get('similarity_threshold', 0.7),
                max_chunk_size=kwargs.get('max_chunk_size', 800),
                min_chunk_size=kwargs.get('min_chunk_size', 100),
                use_simple_fallback=kwargs.get('use_simple_fallback', True)
            )
        elif chunker_type == "chapter":
            return ChapterChunker(
                max_level=kwargs.get('max_level', 3),
                min_chunk_size=kwargs.get('min_chunk_size', 50),
                include_title_in_chunk=kwargs.get('include_title_in_chunk', True)
            )
        elif chunker_type == "parent_child":
            # 获取父子分块器的配置
            parent_type = kwargs.get('parent_type', 'chapter')
            child_type = kwargs.get('child_type', 'chapter')
            parent_kwargs = kwargs.get('parent_kwargs', {})
            child_kwargs = kwargs.get('child_kwargs', {})
            
            # 创建父分块器
            parent_chunker = ChunkerFactory.create_chunker(parent_type, **parent_kwargs)
            
            # 创建子分块器
            child_chunker = ChunkerFactory.create_chunker(child_type, **child_kwargs)
            
            # 创建父子分块器
            return ParentChildChunker(
                parent_chunker=parent_chunker,
                child_chunker=child_chunker,
                overlap_children=kwargs.get('overlap_children', False)
            )
        else:
            raise ValueError(f"未知的分块器类型: {chunker_type}")
    
    @staticmethod
    def get_available_chunkers() -> Dict[str, str]:
        """
        获取可用的分块器类型
        
        Returns:
            分块器类型及描述
        """
        return {
            "fixed": "固定大小分块器，支持重叠",
            "semantic": "语义分块器，基于段落间向量相似度判断语义断裂点",
            "chapter": "章节分块器，按 Markdown 标题层级分割",
            "parent_child": "父子分块器，用子块检索、返回父块（保留上下文）"
        }

import os

def chunk_all_txt_files(
    parser_output_dir="knowledge/parsers/parser_output",
    chunk_output_dir="knowledge/chunkers/chunker_output",
    chunker_type="fixed",
    chunker_kwargs=None
):
    """
    用工厂创建分块器，把 parser_output 里解析好的txt全部切块，保存到 chunker_output

    Args:
        parser_output_dir: 解析后txt文件夹
        chunk_output_dir: 切块结果存储文件夹
        chunker_type: 分块器类型（"fixed" 或 "semantic"）
        chunker_kwargs: 传递给分块器的参数(dict)
    """
    if chunker_kwargs is None:
        chunker_kwargs = {}

    # 不同chunker_type输出到不同子目录
    chunker_type_dir = os.path.join(chunk_output_dir, chunker_type)
    if not os.path.exists(chunker_type_dir):
        os.makedirs(chunker_type_dir, exist_ok=True)

    factory = ChunkerFactory()
    chunker = factory.create_chunker(chunker_type, **chunker_kwargs)

    txt_files = [f for f in os.listdir(parser_output_dir) if f.lower().endswith('.txt')]
    if not txt_files:
        print(f"未找到txt文件在 {parser_output_dir}")
        return

    print(f"在 {parser_output_dir} 共找到 {len(txt_files)} 个txt文件，准备用 {chunker_type} 切块...")

 
    total_chunks = 0
    for i, filename in enumerate(txt_files, 1):
        in_path = os.path.join(parser_output_dir, filename)
        out_filename = os.path.splitext(filename)[0] + "_chunks.txt"
        out_path = os.path.join(chunker_type_dir, out_filename)
        
        try:
            with open(in_path, 'r', encoding='utf-8') as f:
                text = f.read()
            chunks = chunker.chunk(text)
            # 为每一个块分别写入单独的文件
            for j, chunk in enumerate(chunks, 1):
                chunk_filename = os.path.splitext(filename)[0] + f"_chunk_{j}.txt"
                chunk_file_path = os.path.join(chunker_type_dir, chunk_filename)
                with open(chunk_file_path, 'w', encoding='utf-8') as fout:
                    fout.write(chunk)
            
            # 如果是父子分块器，保存父子映射关系到元数据文件
            if chunker_type == "parent_child" and hasattr(chunker, 'child_to_parent_map'):
                import json
                # 将映射关系中的整数键转为字符串（JSON要求）
                child_to_parent_str = {str(k): v for k, v in chunker.child_to_parent_map.items()}
                
                # 生成父块对应的文件名（格式与 chapter 分块一致）
                base_name = os.path.splitext(filename)[0]  # 例如: "xxx_parsed"
                parent_filenames = {}
                for parent_idx in range(len(chunker.parent_chunks)):
                    # 父块文件名：xxx_parsed_chunk_N.txt（N从1开始，与chapter保持一致）
                    parent_filenames[parent_idx] = f"{base_name}_chunk_{parent_idx + 1}.txt"
                
                metadata = {
                    'source_file': filename,
                    'child_to_parent_map': child_to_parent_str,
                    'parent_chunks': chunker.parent_chunks,
                    'parent_filenames': parent_filenames,  # 新增：父块文件名映射
                    'total_children': len(chunks),
                    'total_parents': len(chunker.parent_chunks)
                }
                
                metadata_filename = os.path.splitext(filename)[0] + "_metadata.json"
                metadata_path = os.path.join(chunker_type_dir, metadata_filename)
                with open(metadata_path, 'w', encoding='utf-8') as fout:
                    json.dump(metadata, fout, ensure_ascii=False, indent=2)
                
                print(f"    └─ 已保存父子映射: {len(chunks)} 个子块 → {len(chunker.parent_chunks)} 个父块")
            
            print(f"[{i}/{len(txt_files)}] 已切块: {filename} --> {os.path.relpath(chunker_type_dir, chunk_output_dir)}，共 {len(chunks)} 个块文件")
            total_chunks += len(chunks)
            print(f"共切块: {total_chunks} 个块")
        except Exception as e:
            print(f"[{i}/{len(txt_files)}] 切块失败: {filename}: {e}")

# 如果需要直接运行本文件进行批量切块，可取消以下注释:
if __name__ == "__main__":
    # 可选的分块类型: "fixed", "semantic", "chapter"
    # chunk_all_txt_files(chunker_type="fixed", chunker_kwargs={"chunk_size": 1024, "chunk_overlap": 50})
    from knowledge.embeddings import create_embedder
    # chunk_all_txt_files(chunker_type="semantic", chunker_kwargs={"embedder": create_embedder(method="api"), "similarity_threshold": 0.4, "max_chunk_size": 1536, "min_chunk_size": 100, "use_simple_fallback": True})
    chunk_all_txt_files(chunker_type="parent_child", chunker_kwargs={"parent_type": "chapter", "child_type": "fixed", "parent_kwargs": {"max_level": 3, "min_chunk_size": 50, "include_title_in_chunk": True}, "child_kwargs": {"chunk_size": 512, "chunk_overlap": 50}})