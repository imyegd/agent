# OpenClaw 任务追踪技能

## 概述
自动记录 OpenClaw 每次执行任务的耗时和 token 消耗，生成可分析的效率报告。日志保存在 `D:\code\graduate\llm\trail\openclaw` 目录下。

## 适用场景
- 评估不同任务类型的平均耗时
- 监控 token 消耗趋势，优化成本
- 分析失败任务模式，改进稳定性
- 生成绩效报告用于项目总结

## 工具列表

### 1. track_task_start
**功能**: 开始追踪一个新任务

**参数**:
- `task_name` (必填): 任务名称/描述，如 "数据查询"、"论文改写"
- `metadata` (可选): 额外元数据字典，如 `{"model": "Qwen3.5", "session": "main"}`

**返回结构**:
```json
{
  "success": true,
  "action": "task_started",
  "task_id": "task_20260415_171900_3847",
  "task_name": "数据查询",
  "start_time": "2026-04-15 17:19:00",
  "message": "任务已启动，task_id=..."
}
```

**使用示例**:
- "开始一个数据查询任务"
- "记录任务：论文第 3 章改写"

---

### 2. track_task_complete
**功能**: 标记任务完成并记录 token 消耗

**参数**:
- `input_tokens` (必填): 输入 token 数
- `output_tokens` (必填): 输出 token 数

**返回结构**:
```json
{
  "success": true,
  "action": "task_completed",
  "task_id": "task_20260415_171900_3847",
  "duration_seconds": 12.5,
  "tokens": {
    "input": 150,
    "output": 80,
    "total": 230
  },
  "message": "任务完成，耗时 12.50 秒，共 230 tokens"
}
```

**使用示例**:
- "任务完成了，用了 200 input tokens 和 100 output tokens"

---

### 3. track_task_fail
**功能**: 标记任务失败

**参数**:
- `error_message` (必填): 错误信息
- `input_tokens` (可选): 输入 token 数（失败时可能有部分消耗）
- `output_tokens` (可选): 输出 token 数

**返回结构**:
```json
{
  "success": false,
  "action": "task_failed",
  "task_id": "task_20260415_171900_3847",
  "error": "网络连接超时",
  "message": "任务失败：网络连接超时"
}
```

**使用示例**:
- "任务失败了，报错是 API 连接超时"

---

### 4. get_daily_stats
**功能**: 获取指定日期的任务统计

**参数**:
- `date` (可选): 日期字符串 "YYYY-MM-DD"，不传则使用今天

**返回结构**:
```json
{
  "success": true,
  "action": "get_daily_stats",
  "date": "2026-04-15",
  "stats": {
    "total_tasks": 15,
    "completed_tasks": 14,
    "failed_tasks": 1,
    "running_tasks": 0,
    "success_rate": "93.3%",
    "total_duration_seconds": 185.6,
    "avg_duration_seconds": 13.3,
    "total_input_tokens": 2500,
    "total_output_tokens": 1800,
    "total_tokens": 4300
  }
}
```

**使用示例**:
- "今天总共跑了多少任务？"
- "查看 2026-04-15 的统计数据"

---

## 日志文件结构

每日日志文件命名格式：`task_log_YYYYMMDD.json`

```json
{
  "log_date": "2026-04-15",
  "generated_at": "2026-04-15 18:30:00",
  "summary": { ... },  // 当日统计摘要
  "records": [         // 每条任务记录
    {
      "task_id": "task_20260415_171900_3847",
      "task_name": "束流数据查询",
      "start_time": "2026-04-15 17:19:00",
      "end_time": "2026-04-15 17:19:12",
      "duration_seconds": 12.5,
      "input_tokens": 150,
      "output_tokens": 80,
      "total_tokens": 230,
      "status": "completed",
      "error_message": null,
      "metadata": {}
    }
  ]
}
```

---

## 工作流程建议

### 典型任务流程
```
1. 用户请求 → 调用 track_task_start(task_name)
2. 执行任务 → （可选）update_tokens 跟踪中间状态
3. 完成任务 → 调用 track_task_complete(input_tokens, output_tokens)
   或
3. 失败处理 → 调用 track_task_fail(error_message, ...)
```

### Token 获取方式
- **会话中**: 通过 `session_status` 工具的 `usage` 字段获取
- **手动估算**: 根据模型定价标准推算
- **API 响应**: 从 LLM API 返回的 `usage` 字段提取

---

## 注意事项
- 每个任务必须有明确的 start 和 complete/fail 配对调用
- 失败任务也会写入日志，便于后续分析
- 日志按日期自动分文件，避免单文件过大
- metadata 字段可以记录 model、session 类型等上下文信息

---

## 依赖文件
- 核心代码：`D:\code\graduate\llm\trail\openclaw\task_tracker.py`
- 日志目录：`D:\code\graduate\llm\trail\openclaw\`
