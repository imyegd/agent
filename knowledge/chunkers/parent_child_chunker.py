"""父子分块器"""
from typing import List, Dict, Tuple, Optional
import os
import sys
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from knowledge.chunkers.base_chunker import BaseChunker
    from knowledge.chunkers.fixed_size_chunker import FixedSizeChunker
    from knowledge.chunkers.semantic_chunker import SemanticChunker
    from knowledge.chunkers.chapter_chunker import ChapterChunker
else:
    from .base_chunker import BaseChunker
    from .fixed_size_chunker import FixedSizeChunker
    from .semantic_chunker import SemanticChunker
    from .chapter_chunker import ChapterChunker

class ParentChildChunker(BaseChunker):
    """
    父子分块器：用细粒度的子块进行检索，返回包含更多上下文的父块
    
    这种策略的优势：
    1. 检索时使用子块，匹配更精准
    2. 返回时使用父块，保留更多上下文信息
    3. 避免因块太大而导致检索不准确，又避免因块太小而丢失上下文
    """
    
    def __init__(
        self,
        parent_chunker: BaseChunker,
        child_chunker: BaseChunker,
        overlap_children: bool = False
    ):
        """
        初始化父子分块器
        
        Args:
            parent_chunker: 用于生成父块的分块器（较大的块）
            child_chunker: 用于生成子块的分块器（较小的块）
            overlap_children: 子块是否可以跨越父块边界（默认 False）
        """
        self.parent_chunker = parent_chunker
        self.child_chunker = child_chunker
        self.overlap_children = overlap_children
        
        # 存储最近一次分块的父子关系
        self.parent_chunks: List[str] = []
        self.child_to_parent_map: Dict[int, int] = {}
    
    def chunk(self, text: str) -> List[str]:
        """
        执行父子分块，返回子块列表（用于检索）
        
        Args:
            text: 输入文本
            
        Returns:
            子块列表（用于向量化和检索）
        """
        if not text or not text.strip():
            return []
        
        # 1. 使用父分块器生成父块
        self.parent_chunks = self.parent_chunker.chunk(text)
        
        if not self.parent_chunks:
            return []
        
        # 2. 对每个父块生成子块
        child_chunks = []
        self.child_to_parent_map = {}
        
        for parent_idx, parent_chunk in enumerate(self.parent_chunks):
            # 对父块进行子分块
            children = self.child_chunker.chunk(parent_chunk)
            
            # 记录每个子块对应的父块索引
            for child in children:
                if child.strip():  # 只保留非空子块
                    child_idx = len(child_chunks)
                    child_chunks.append(child)
                    self.child_to_parent_map[child_idx] = parent_idx
        
        return child_chunks
    
    def get_parent_chunk(self, child_index: int) -> Optional[str]:
        """
        根据子块索引获取对应的父块
        
        Args:
            child_index: 子块在列表中的索引
            
        Returns:
            对应的父块内容，如果索引无效则返回 None
        """
        if child_index not in self.child_to_parent_map:
            return None
        
        parent_idx = self.child_to_parent_map[child_index]
        
        if 0 <= parent_idx < len(self.parent_chunks):
            return self.parent_chunks[parent_idx]
        
        return None
    
    def get_parent_chunks(self, child_indices: List[int]) -> List[str]:
        """
        根据多个子块索引获取对应的父块（自动去重）
        
        Args:
            child_indices: 子块索引列表
            
        Returns:
            对应的父块列表（已去重）
        """
        parent_indices = set()
        for child_idx in child_indices:
            if child_idx in self.child_to_parent_map:
                parent_indices.add(self.child_to_parent_map[child_idx])
        
        parent_chunks = []
        for parent_idx in sorted(parent_indices):
            if 0 <= parent_idx < len(self.parent_chunks):
                parent_chunks.append(self.parent_chunks[parent_idx])
        
        return parent_chunks
    
    def chunk_with_metadata(self, text: str) -> Tuple[List[str], List[Dict]]:
        """
        执行分块并返回完整的元数据信息
        
        Args:
            text: 输入文本
            
        Returns:
            (子块列表, 元数据列表)
            元数据包含: {'parent_index': int, 'parent_chunk': str, 'child_index': int}
        """
        child_chunks = self.chunk(text)
        
        metadata = []
        for child_idx, child_chunk in enumerate(child_chunks):
            parent_idx = self.child_to_parent_map.get(child_idx)
            parent_chunk = self.get_parent_chunk(child_idx)
            
            metadata.append({
                'child_index': child_idx,
                'parent_index': parent_idx,
                'parent_chunk': parent_chunk,
                'child_chunk': child_chunk
            })
        
        return child_chunks, metadata
    
    def get_statistics(self) -> Dict:
        """
        获取分块统计信息
        
        Returns:
            统计信息字典
        """
        if not self.parent_chunks or not self.child_to_parent_map:
            return {
                'parent_count': 0,
                'child_count': 0,
                'avg_children_per_parent': 0
            }
        
        # 统计每个父块的子块数量
        children_per_parent = {}
        for child_idx, parent_idx in self.child_to_parent_map.items():
            children_per_parent[parent_idx] = children_per_parent.get(parent_idx, 0) + 1
        
        return {
            'parent_count': len(self.parent_chunks),
            'child_count': len(self.child_to_parent_map),
            'avg_children_per_parent': len(self.child_to_parent_map) / len(self.parent_chunks),
            'children_distribution': children_per_parent
        }


if __name__ == "__main__":
    pass
