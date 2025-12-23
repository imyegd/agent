"""PDF文档解析器"""
import os
import sys

# 支持直接运行和作为模块导入
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from knowledge.parsers.base_parser import BaseParser
else:
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


def main():
    """测试PDF解析器"""
    print("="*60)
    print("PDF解析器测试")
    print("="*60 + "\n")
    
    # PDF文件目录
    data_dir = "knowledge/data"
    
    if not os.path.exists(data_dir):
        print(f"错误: 数据目录不存在: {data_dir}")
        return
    
    # 查找所有PDF文件
    pdf_files = [f for f in os.listdir(data_dir) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print(f"未找到PDF文件在 {data_dir}")
        return
    
    print(f"找到 {len(pdf_files)} 个PDF文件\n")
    
    # 创建解析器
    parser = PdfParser()
    
    # 创建输出目录
    output_dir = "knowledge/parsers/test_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存所有解析结果
    all_texts = {}
    
    # 测试每个PDF
    for i, filename in enumerate(pdf_files, 1):
        file_path = os.path.join(data_dir, filename)
        
        print(f"\n[{i}/{len(pdf_files)}] 解析: {filename}")
        print("-" * 60)
        
        text = parser.parse(file_path)
        
        if text:
            # 保存文本
            all_texts[filename] = text
            
            # 保存到txt文件
            output_filename = os.path.splitext(filename)[0] + "_parsed.txt"
            output_path = os.path.join(output_dir, output_filename)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            # 显示统计信息
            lines = text.split('\n')
            words = len(text.split())
            
            print(f"[OK] 成功!")
            print(f"  字符数: {len(text)}")
            print(f"  行数: {len(lines)}")
            print(f"  词数: {words}")
            print(f"  已保存到: {output_path}")
            
            # 显示前200个字符作为预览
            preview = text[:200].replace('\n', ' ')
            print(f"\n  预览: {preview}...")
        else:
            print(f"[FAIL] 解析失败或无内容")
    
    print("\n" + "="*60)
    print("测试完成!")
    print(f"共解析 {len(all_texts)} 个PDF文件")
    print(f"文本已保存到: {output_dir}")
    print("="*60)
    
    return all_texts


if __name__ == "__main__":
    main()

