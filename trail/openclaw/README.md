# OpenClaw 任务追踪器 - 使用说明

## 🎯 快速开始（推荐）

### 一键生成今日报告

```powershell
D:\code\graduate\llm\trail\openclaw\daily_report.ps1
```

**输出示例：**
```json
{
  "date": "2026-04-15",
  "total_tools_called": 53,
  "tools_breakdown": [
    {"tool": "exec", "count": 31},
    {"tool": "write", "count": 11},
    {"tool": "read", "count": 5}
  ],
  "success_rate": "100.0%"
}
```

---

## 📁 文件说明

| 文件 | 作用 |
|------|------|
| `parse_openclaw_logs.py` | **核心脚本** - 直接从 OpenClaw 日志提取统计信息 |
| `daily_report.ps1` | 一键运行脚本（PowerShell） |
| `full_session_tracker.py` | 可选：手动记录工具调用（如果想在代码内追踪） |
| `monitor_openclaw.py` | 装饰器方式追踪（进阶用法） |
| `tool_calls.db` | SQLite 数据库（自动创建，存储历史统计） |

---

## 🔧 使用方式

### 方式 1: 自动解析日志（推荐）

**优点**：无需修改代码，自动从 OpenClaw 会话日志读取

```powershell
# 今日统计
D:\code\graduate\llm\trail\openclaw\daily_report.ps1

# 只分析不保存
python trail\openclaw\parse_openclaw_logs.py --analyze

# 列出所有会话文件
python trail\openclaw\parse_openclaw_logs.py --show-session-files
```

### 方式 2: 手动记录（适合特定场景）

```powershell
python trail\openclaw\record_session.py "束流数据查询" 300 200
```

### 方式 3: Python 代码内追踪

```python
from trail.openclaw.full_session_tracker import FullSessionTracker

tracker = FullSessionTracker()
tracker.start_session("用户提示")
tracker.record_tool_start("read", {"path": "test.txt"})
tracker.record_tool_end(call_id, result)
tracker.end_session(input_tokens=300, output_tokens=200)
```

---

## 📊 查看统计

```powershell
# 今日统计
python trail\openclaw\parse_openclaw_logs.py --save

# 数据库中的历史统计
python trail\openclaw\full_session_tracker.py stats --date 2026-04-15
```

---

## 💡 原理说明

OpenClaw 自动把所有对话记录到 `.jsonl` 文件：
```
C:\Users\jinta\.openclaw\agents\main\sessions\<session-id>.jsonl
```

每条记录包含：
- 工具调用 (`toolCall`)
- 工具结果 + 耗时 (`toolResult` + `durationMs`)  
- Token 消耗 (`usage.input` / `usage.output`)

`parse_openclaw_logs.py` 直接解析这些日志文件，自动聚合统计。

---

## ⚠️ 注意事项

1. **Token 数显示为 0**？某些版本的 OpenClaw 不记录详细 token，这是正常的。可以用手动方式补充。

2. **只能看到最近的会话**？脚本默认扫描最近 24 小时的会话，防止分析过多历史数据。

3. **想保留更详细的每条工具记录**？可以使用 `--save` 参数存入 SQLite 数据库。

---

## 🛠 进阶配置

### 修改日志路径

编辑 `parse_openclaw_logs.py`：
```python
LOG_DIR = r"C:\你的\自定义\路径\sessions"
```

### 设置定时报告

用 Windows 任务计划程序每天执行：
```powershell
schtasks /create /sc daily /st 09:00 /tn "OpenClaw Daily Report" /tr "powershell -ExecutionPolicy Bypass -File D:\code\graduate\llm\trail\openclaw\daily_report.ps1"
```
