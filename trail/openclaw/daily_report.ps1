# OpenClaw 每日统计报告
# 用法：.\daily_report.ps1

$ErrorActionPreference = "Stop"
Set-Location D:\code\graduate\llm

Write-Host "=== OpenClaw 工具调用统计 ===" -ForegroundColor Cyan
Write-Host ""

# 运行 Python 分析脚本
python trail\openclaw\parse_openclaw_logs.py --save

Write-Host ""
Write-Host "查看历史记录:" -ForegroundColor Yellow
Write-Host "  python trail\openclaw\full_session_tracker.py stats --date 2026-04-15"
