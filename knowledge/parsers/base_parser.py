"""解析器基类"""
from abc import ABC, abstractmethod


class BaseParser(ABC):
    """文档解析器抽象基类"""
    
    @abstractmethod
    def parse(self, file_path: str) -> str:
        """
        解析文档并返回文本内容
        
        Args:
            file_path: 文档路径
            
        Returns:
            提取的文本内容
        """
        pass

