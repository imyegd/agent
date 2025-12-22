"""分块器基类"""
from abc import ABC, abstractmethod
from typing import List


class BaseChunker(ABC):
    """文本分块器抽象基类"""
    
    @abstractmethod
    def chunk(self, text: str) -> List[str]:
        """
        将文本分割成块
        
        Args:
            text: 输入文本
            
        Returns:
            文本块列表
        """
        pass

