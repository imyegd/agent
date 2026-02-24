"""
主程序入口
提供命令行交互界面，支持自然语言查询束流数据
"""

from agents import BeamDataAgent, StreamingBeamDataAgent
from config import Config
import sys


def print_banner():
    """打印欢迎信息"""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║          束流数据智能查询系统 v1.0                        ║
║          Beam Data Intelligent Query System               ║
╚═══════════════════════════════════════════════════════════╝

说明：
  - 您可以用自然语言查询束流数据
  - 例如："查询2025年8月31日两点到三点的束流数据"
  - 输入 'exit' 或 'quit' 退出程序
  - 输入 'reset' 清空对话历史
  - 输入 'help' 查看帮助信息

═══════════════════════════════════════════════════════════════
"""
    print(banner)


def print_help():
    """打印帮助信息"""
    help_text = """
【帮助信息】

1. 查询示例：
   - "取出2025年8月31日两点钟到三点钟的束流数据"
   - "查询8月30日下午5点到6点的数据"
   - "显示2025-08-30 17:23:26到17:23:30的记录"
   - "数据集有多少条记录？"
   - "数据的时间范围是什么？"

2. 支持的命令：
   - exit/quit: 退出程序
   - reset: 清空对话历史，开始新的对话
   - help: 显示此帮助信息

3. 注意事项：
   - 系统会自动理解您的时间表达
   - 查询结果包含数据条数、统计信息等
   - 支持上下文对话，可以追问相关问题
"""
    print(help_text)


def main():
    """主函数"""
    # 打印欢迎信息
    print_banner()
    
    # 初始化配置
    config = Config.get_api_config()
    
    # 创建代理
    print("正在初始化系统...")
    try:
        agent = BeamDataAgent(
            api_key=config['api_key'],
            base_url=config['base_url'],
            model=config['model']
        )
        print("✓ 系统初始化成功！\n")
    except Exception as e:
        print(f"✗ 系统初始化失败: {e}")
        sys.exit(1)
    
    # 开始对话循环
    while True:
        try:
            # 获取用户输入
            user_input = input("\n您: ").strip()
            
            # 处理特殊命令
            if user_input.lower() in ['exit', 'quit', '退出']:
                print("\n感谢使用！再见！👋")
                break
            
            if user_input.lower() in ['reset', '重置']:
                agent.reset_conversation()
                print("✓ 对话历史已清空")
                continue
            
            if user_input.lower() in ['help', '帮助']:
                print_help()
                continue
            
            if not user_input:
                continue
            
            # 调用代理处理用户输入
            print("\n助手: ", end="", flush=True)
            response = agent.chat(user_input)
            print(response)
            
        except KeyboardInterrupt:
            print("\n\n检测到中断，正在退出...")
            break
        except Exception as e:
            print(f"\n✗ 发生错误: {e}")
            print("请重试或输入 'help' 查看帮助")


def main_stream():
    """主函数（流式输出版本）"""
    # 打印欢迎信息
    print_banner()
    
    # 初始化配置
    config = Config.get_api_config()
    
    # 创建代理（流式版本）
    print("正在初始化系统...")
    try:
        agent = StreamingBeamDataAgent(
            api_key=config['api_key'],
            base_url=config['base_url'],
            model=config['model']
        )
        print("✓ 系统初始化成功！\n")
    except Exception as e:
        print(f"✗ 系统初始化失败: {e}")
        sys.exit(1)
    
    # 开始对话循环
    while True:
        try:
            # 获取用户输入
            user_input = input("\n您: ").strip()
            
            # 处理特殊命令
            if user_input.lower() in ['exit', 'quit', '退出']:
                print("\n感谢使用！再见！👋")
                break
            
            if user_input.lower() in ['reset', '重置']:
                agent.reset_conversation()
                print("✓ 对话历史已清空")
                continue
            
            if user_input.lower() in ['help', '帮助']:
                print_help()
                continue
            
            if not user_input:
                continue
            
            # 调用代理处理用户输入（流式）
            print("\n助手: ", end="", flush=True)
            for chunk in agent.chat_stream(user_input):
                print(chunk, end="", flush=True)
            print()  # 换行
            
        except KeyboardInterrupt:
            print("\n\n检测到中断，正在退出...")
            break
        except Exception as e:
            print(f"\n✗ 发生错误: {e}")
            print("请重试或输入 'help' 查看帮助")


if __name__ == "__main__":
    # 可以通过命令行参数选择是否使用流式输出
    if len(sys.argv) > 1 and sys.argv[1] == "--stream":
        main_stream()
    else:
        main()

