"""PDF文档解析器"""
from .base_parser import BaseParser


class PdfParser(BaseParser):
    """PDF文件解析器，使用PyMuPDF"""
    
    def __init__(self):
        try:
            import fitz
            self.fitz = fitz
        except ImportError:
            raise ImportError("需要安装 PyMuPDF: pip install pymupdf")
    
    def parse(self, file_path: str) -> str:
        """
        解析PDF文件
        
        Args:
            file_path: PDF文件路径
            
        Returns:
            提取的文本内容
        """
        try:
            doc = self.fitz.open(file_path)
            text = ""
            
            for page_num, page in enumerate(doc, 1):
                page_text = page.get_text()
                text += page_text
                
            doc.close()
            
            # 清理文本
            text = text.strip()
            
            if not text:
                print(f"警告: {file_path} PDF无文本内容")
                return ""
            
            print(f"成功解析 {file_path}: {len(text)} 字符, {page_num} 页")
            return text
            
        except Exception as e:
            print(f"解析PDF文件失败 {file_path}: {e}")
            return ""

