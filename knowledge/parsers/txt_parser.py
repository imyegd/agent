"""TXT文档解析器"""
from .base_parser import BaseParser


class TxtParser(BaseParser):
    """TXT文件解析器"""
    
    def parse(self, file_path: str) -> str:
        """
        解析TXT文件
        
        Args:
            file_path: TXT文件路径
            
        Returns:
            文本内容
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 清理文本
            content = content.strip()
            
            if not content:
                print(f"警告: {file_path} 文件为空")
                return ""
            
            print(f"成功解析 {file_path}: {len(content)} 字符")
            return content
            
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    content = f.read().strip()
                print(f"成功解析 {file_path} (GBK编码): {len(content)} 字符")
                return content
            except Exception as e:
                print(f"解析TXT文件失败 {file_path}: {e}")
                return ""
        except Exception as e:
            print(f"解析TXT文件失败 {file_path}: {e}")
            return ""

