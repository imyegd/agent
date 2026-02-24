"""TXT文档解析器"""
import os
import sys

# 支持直接运行和作为模块导入
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from knowledge.parsers.base_parser import BaseParser
else:
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


def main():
    """测试TXT解析器"""
    print("="*60)
    print("TXT解析器测试")
    print("="*60 + "\n")
    
    # TXT文件目录
    data_dir = "knowledge/data"
    
    if not os.path.exists(data_dir):
        print(f"错误: 数据目录不存在: {data_dir}")
        return
    
    # 查找所有TXT文件
    txt_files = [f for f in os.listdir(data_dir) if f.lower().endswith('.txt')]
    
    if not txt_files:
        print(f"未找到TXT文件在 {data_dir}")
        return
    
    print(f"找到 {len(txt_files)} 个TXT文件\n")
    
    # 创建解析器
    parser = TxtParser()
    
    # 测试每个TXT
    for i, filename in enumerate(txt_files, 1):
        file_path = os.path.join(data_dir, filename)
        
        print(f"\n[{i}/{len(txt_files)}] 解析: {filename}")
        print("-" * 60)
        
        text = parser.parse(file_path)
        
        if text:
            # 显示统计信息
            lines = text.split('\n')
            words = len(text.split())
            
            print(f"[OK] 成功!")
            print(f"  字符数: {len(text)}")
            print(f"  行数: {len(lines)}")
            print(f"  词数: {words}")
            
            # 显示前200个字符作为预览
            preview = text[:200].replace('\n', ' ')
            print(f"\n  预览: {preview}...")
        else:
            print(f"[FAIL] 解析失败或无内容")
    
    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)


if __name__ == "__main__":
    main()

