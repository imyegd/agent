"""解析器工厂"""
import os
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# 支持直接运行：添加项目根目录到路径
_current_file = Path(__file__).resolve()
_project_root = _current_file.parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# 尝试相对导入，失败则使用绝对导入
if __name__ == "__main__":
    from knowledge.parsers.base_parser import BaseParser
    from knowledge.parsers.txt_parser import TxtParser
    from knowledge.parsers.pdf_parser import PdfParser
    from knowledge.parsers.pdf_parser_api import MinerUPdfParser
else:
    from .base_parser import BaseParser
    from .txt_parser import TxtParser
    from .pdf_parser import PdfParser
    from .pdf_parser_api import MinerUPdfParser

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


def parse_all_pdf_files(
    input_dir: str = "knowledge/data",
    output_dir: str = "knowledge/parsers/parser_output",
    use_api: bool = True,
    file_pattern: str = "*.pdf"
):
    """
    批量解析指定目录下的所有 PDF 文件
    
    Args:
        input_dir: 输入目录，包含待解析的 PDF 文件
        output_dir: 输出目录，保存解析后的文本文件
        use_api: 是否优先使用 MinerU API（如果可用）
        file_pattern: 文件匹配模式，默认 "*.pdf"
    """
    import glob
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 查找所有 PDF 文件
    search_pattern = os.path.join(input_dir, "**", file_pattern)
    pdf_files = glob.glob(search_pattern, recursive=True)
    
    if not pdf_files:
        print(f"未找到 PDF 文件在 {input_dir}")
        return
    
    print(f"=" * 60)
    print(f"批量 PDF 解析")
    print(f"=" * 60)
    print(f"输入目录: {input_dir}")
    print(f"输出目录: {output_dir}")
    print(f"找到 {len(pdf_files)} 个 PDF 文件")
    
    # 确定使用的解析器
    parser = None
    if use_api:
        mineru_api_key = os.getenv("MINERU_API_KEY")
        if mineru_api_key:
            try:
                
                parser = MinerUPdfParser()
                print(f"解析器: MinerU API")
            except Exception as e:
                print(f"MinerU API 初始化失败: {e}")
                print(f"降级到本地 PyMuPDF 解析器")
    
    if parser is None:
        parser = PdfParser()
        print(f"解析器: 本地 PyMuPDF")
    
    print(f"=" * 60)
    print()
    
    # 统计信息
    success_count = 0
    failed_count = 0
    failed_files = []
    
    # 批量解析
    for i, file_path in enumerate(pdf_files, 1):
        filename = os.path.basename(file_path)
        print(f"[{i}/{len(pdf_files)}] 解析: {filename}")
        print("-" * 60)
        
        try:
            # 解析文档
            text = parser.parse(file_path)
            
            if text:
                # 保存到输出目录
                output_filename = os.path.splitext(filename)[0] + "_parsed.txt"
                output_path = os.path.join(output_dir, output_filename)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                
                success_count += 1
                print(f"[成功] 解析完成: {len(text)} 字符")
                print(f"  输出文件: {output_filename}")
                print(f"  前100字符: {text[:100].replace(chr(10), ' ')}")
            else:
                failed_count += 1
                failed_files.append(filename)
                print(f"[失败] 解析失败: 无内容返回")
        
        except Exception as e:
            failed_count += 1
            failed_files.append(filename)
            print(f"[失败] 解析失败: {e}")
        
        print()
    
    # 输出统计结果
    print("=" * 60)
    print("解析统计")
    print("=" * 60)
    print(f"总文件数: {len(pdf_files)}")
    print(f"成功: {success_count}")
    print(f"失败: {failed_count}")
    
    if failed_files:
        print(f"\n失败的文件:")
        for f in failed_files:
            print(f"  - {f}")
    
    print("=" * 60)


def parse_single_pdf(
    pdf_path: str,
    output_path: Optional[str] = None,
    use_api: bool = True
) -> bool:
    """
    解析单个 PDF 文件
    
    Args:
        pdf_path: PDF 文件路径
        output_path: 可选的输出文件路径，如果不提供则自动生成
        use_api: 是否优先使用 MinerU API
        
    Returns:
        是否解析成功
    """
    if not os.path.exists(pdf_path):
        print(f"文件不存在: {pdf_path}")
        return False
    
    # 确定输出路径
    if output_path is None:
        base_dir = os.path.dirname(pdf_path)
        filename = os.path.basename(pdf_path)
        output_filename = os.path.splitext(filename)[0] + "_parsed.txt"
        output_path = os.path.join(base_dir, output_filename)
    
    # 确定解析器
    parser = None
    if use_api:
        mineru_api_key = os.getenv("MINERU_API_KEY")
        if mineru_api_key:
            try:
                from .pdf_parser_api import MinerUPdfParser
                parser = MinerUPdfParser()
                print(f"使用 MinerU API 解析器")
            except Exception as e:
                print(f"MinerU API 初始化失败，降级到本地解析器")
    
    if parser is None:
        parser = PdfParser()
        print(f"使用本地 PyMuPDF 解析器")
    
    # 解析
    try:
        print(f"\n解析文件: {pdf_path}")
        text = parser.parse(pdf_path)
        
        if text:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            print(f"[成功] 解析完成")
            print(f"  字符数: {len(text)}")
            print(f"  输出: {output_path}")
            return True
        else:
            print(f"[失败] 解析失败: 无内容返回")
            return False
    
    except Exception as e:
        print(f"✗ 解析失败: {e}")
        return False


# 如果需要直接运行本文件进行批量解析，可取消以下注释或修改参数:
if __name__ == "__main__":
    # 批量解析所有 PDF 文件
    parse_all_pdf_files(
        input_dir="knowledge/data/books",
        output_dir="knowledge/parsers/parser_output/books",
        use_api=True  # True=使用API, False=使用本地解析器
    )