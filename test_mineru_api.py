"""测试MinerU API PDF解析器"""
import os

print("="*60)
print("MinerU API PDF解析器测试")
print("="*60 + "\n")

# 1. 检查API密钥
api_key = os.getenv("MINERU_API_KEY")

if not api_key:
    print("⚠️  未设置API密钥")
    print("\n请先设置环境变量:")
    print("  Windows CMD:        set MINERU_API_KEY=你的密钥")
    print("  Windows PowerShell: $env:MINERU_API_KEY='你的密钥'")
    print("  Linux/Mac:          export MINERU_API_KEY='你的密钥'")
    print("\n或者在代码中直接指定:")
    print("  parser = MinerUPdfParser(api_key='你的密钥')")
    exit(1)

print(f"✓ API密钥已设置: {api_key[:10]}...")

# 2. 测试解析器
from knowledge.parsers.pdf_parser_api import MinerUPdfParser, HybridPdfParser

# 测试文件
test_file = "knowledge/data/95MeV／u的~（12）C炮弹产生的二次束流强度研究_杨永锋.pdf"

if not os.path.exists(test_file):
    # 尝试找第一个PDF
    data_dir = "knowledge/data"
    pdf_files = [f for f in os.listdir(data_dir) if f.lower().endswith('.pdf')]
    if pdf_files:
        test_file = os.path.join(data_dir, pdf_files[0])
    else:
        print(f"错误: 未找到测试PDF文件")
        exit(1)

print(f"\n测试文件: {os.path.basename(test_file)}")

# 3. 方式一：纯API解析
print("\n" + "="*60)
print("方式一：纯API解析")
print("="*60)

try:
    parser1 = MinerUPdfParser(api_key=api_key)
    text1 = parser1.parse(test_file)
    
    if text1:
        print(f"\n✓ 解析成功!")
        print(f"  字符数: {len(text1)}")
        print(f"  行数: {len(text1.splitlines())}")
        print(f"\n  预览前200字符:")
        print(f"  {text1[:200]}...")
    else:
        print("✗ 解析失败")
        
except Exception as e:
    print(f"✗ 错误: {e}")

# 4. 方式二：混合解析（推荐）
print("\n" + "="*60)
print("方式二：混合解析（API优先，本地降级）")
print("="*60)

try:
    parser2 = HybridPdfParser(
        api_key=api_key,
        use_api=True,
        fallback_to_local=True
    )
    
    text2 = parser2.parse(test_file)
    
    if text2:
        print(f"\n✓ 解析成功!")
        print(f"  字符数: {len(text2)}")
        print(f"  行数: {len(text2.splitlines())}")
    else:
        print("✗ 解析失败")
        
except Exception as e:
    print(f"✗ 错误: {e}")

# 5. 方式三：通过工厂类（最简单）
print("\n" + "="*60)
print("方式三：通过工厂类自动选择")
print("="*60)

from knowledge.parsers import ParserFactory

text3 = ParserFactory.parse_document(test_file)

if text3:
    print(f"\n✓ 解析成功!")
    print(f"  字符数: {len(text3)}")
    print(f"  行数: {len(text3.splitlines())}")
else:
    print("✗ 解析失败")

print("\n" + "="*60)
print("测试完成!")
print("="*60)

