"""分块器工厂"""
from typing import Dict, Any
from .base_chunker import BaseChunker
from .fixed_size_chunker import FixedSizeChunker
from .semantic_chunker import SemanticChunker


class ChunkerFactory:
    """分块器工厂类"""
    
    @staticmethod
    def create_chunker(chunker_type: str = "fixed", **kwargs) -> BaseChunker:
        """
        创建指定类型的分块器
        
        Args:
            chunker_type: 分块器类型，可选 "fixed", "semantic"
            **kwargs: 传递给分块器的参数
            
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
                max_chunk_size=kwargs.get('max_chunk_size', 800),
                min_chunk_size=kwargs.get('min_chunk_size', 100)
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
            "semantic": "语义分块器，按段落和句子分割"
        }

