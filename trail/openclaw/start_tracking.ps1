# OpenClaw 对话追踪启动脚本
# 运行此脚本后，会在当前 PowerShell 会话中加载追踪器

$ErrorActionPreference = "Stop"

# 切换到项目目录
Set-Location D:\code\graduate\llm

# 加载追踪器模块
Write-Host "[INFO] 正在初始化 OpenClaw 任务追踪器..." -ForegroundColor Cyan

try {
    # 导入 Python 模块
    & python -c "
import sys
sys.path.insert(0, r'D:\code\graduate\llm')
from trail.openclaw.auto_tracker_hook import AutoTaskTracker
import json

# 创建全局追踪器实例
if 'tracker' not in dir():
    global tracker
    tracker = AutoTaskTracker()

print('[OK] 追踪器已就绪')
print('[TIP] 使用前调用：on_dialogue_start(\"你的消息\")')
print('[TIP] 使用后调用：on_dialogue_end(input_tokens=X, output_tokens=Y)')
"

    Write-Host "[OK] 环境准备完成" -ForegroundColor Green
    Write-Host ""
    Write-Host "使用方法：" -ForegroundColor Yellow
    Write-Host "  开始对话前：python -c \"...on_dialogue_start('你的消息')\"" 
    Write-Host "  结束对话后：python -c \"...on_dialogue_end(input_tokens=X, output_tokens=Y)\"" 
    Write-Host ""
    Write-Host "查看今日统计：python -c \"from trail.openclaw.task_tracker import get_daily_stats; import json; print(json.dumps(get_daily_stats(), ensure_ascii=False, indent=2))\"" -ForegroundColor Gray
    
} catch {
    Write-Host "[ERROR] 初始化失败：$_" -ForegroundColor Red
    exit 1
}
