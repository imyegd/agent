"""固定大小分块器"""
from typing import List
from .base_chunker import BaseChunker


class FixedSizeChunker(BaseChunker):
    """固定大小的文本分块器，支持重叠"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        初始化固定大小分块器
        
        Args:
            chunk_size: 每个块的字符数
            chunk_overlap: 块之间的重叠字符数
        """
        if chunk_size <= 0:
            raise ValueError("chunk_size必须为正数")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap不能为负数")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap必须小于chunk_size")
        
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk(self, text: str) -> List[str]:
        """
        将文本分割成固定大小的块
        
        Args:
            text: 输入文本
            
        Returns:
            文本块列表
        """
        if not text or not text.strip():
            return []
        
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            chunk = text[start:end].strip()
            
            if chunk:  # 只添加非空块
                chunks.append(chunk)
            
            # 计算下一个起始位置
            start += self.chunk_size - self.chunk_overlap
            
            # 避免无限循环
            if start <= end - self.chunk_size + self.chunk_overlap:
                start = end
        
        return chunks

