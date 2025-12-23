"""解析器工厂"""
import os
from typing import Optional
from dotenv import load_dotenv
from .base_parser import BaseParser
from .txt_parser import TxtParser
from .pdf_parser import PdfParser

# 加载环境变量
load_dotenv()


class ParserFactory:
    """文档解析器工厂类"""
    
    @staticmethod
    def _get_pdf_parser():
        """动态选择PDF解析器 - 优先API，降级本地"""
        # 检查是否配置了MinerU API
        mineru_api_key = os.getenv("MINERU_API_KEY")
        
        if mineru_api_key:
            try:
                from .pdf_parser_api import MinerUPdfParser
                print("[ParserFactory] 使用 MinerU API 解析器")
                return MinerUPdfParser()
            except Exception as e:
                print(f"[ParserFactory] MinerU API 初始化失败: {e}")
                print("[ParserFactory] 降级到本地 PyMuPDF 解析器")
        
        # 默认使用本地PyMuPDF
        print("[ParserFactory] 使用本地 PyMuPDF 解析器")
        return PdfParser()
    
    _parsers = {
        '.txt': TxtParser,
        '.pdf': None,  # 动态选择
    }
    
    @classmethod
    def parse_document(cls, file_path: str) -> Optional[str]:
        """
        根据文件扩展名自动选择解析器并解析文档
        
        Args:
            file_path: 文档路径
            
        Returns:
            提取的文本内容，失败返回None
        """
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        # 对于PDF，动态选择
        if ext == '.pdf':
            try:
                parser = cls._get_pdf_parser()
                return parser.parse(file_path)
            except Exception as e:
                print(f"解析文档失败 {file_path}: {e}")
                return None
        
        # 其他文件类型
        parser_class = cls._parsers.get(ext)
        
        if parser_class is None:
            print(f"不支持的文件类型: {ext}")
            return None
        
        try:
            parser = parser_class()
            return parser.parse(file_path)
        except Exception as e:
            print(f"解析文档失败 {file_path}: {e}")
            return None
    
    @classmethod
    def get_parser(cls, file_type: str) -> Optional[BaseParser]:
        """
        获取指定类型的解析器实例
        
        Args:
            file_type: 文件类型，如 '.pdf', '.txt'
            
        Returns:
            解析器实例
        """
        parser_class = cls._parsers.get(file_type.lower())
        if parser_class:
            return parser_class()
        return None

