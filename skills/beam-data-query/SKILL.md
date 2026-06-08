# 束流数据查询技能

## 概述
提供对工业装备束流数据的查询和元信息获取能力。基于 CSV 数据文件和 Pandas 实现，支持时间范围查询、列筛选、统计信息返回等功能。

## 适用场景
- 查询指定时间段内的束流运行数据
- 获取数据集的基本信息和元数据
- 在异常诊断前进行数据核对和取样
- 趋势分析前的数据预览

## 工具列表

### 1. query_beam_data
**功能**: 按时间范围查询束流数据，支持列筛选、条数限制、统计信息

**参数**:
- `start_time` (必填): 开始时间，格式 "YYYY-MM-DD HH:MM:SS" 或 "YYYY-MM-DDTHH:MM:SS"
- `end_time` (必填): 结束时间，格式同上
- `columns` (可选): 需要返回的列名列表，如 ["时间", "target", "feature1"]
- `limit` (可选): 返回样本条数上限，范围 1-200，默认 20
- `include_statistics` (可选): 是否返回 target 统计信息，默认 true

**返回结构**:
```json
{
  "success": true,
  "tool": "query_beam_data",
  "message": "查询成功",
  "query": { "start_time": "...", "end_time": "...", "columns": [...], "limit": 20 },
  "summary": {
    "matched_records": 60,
    "returned_records": 20,
    "selected_columns": [...],
    "dataset_time_range": { "start": "...", "end": "..." }
  },
  "statistics": {
    "target_mean": 123.45,
    "target_max": 156.78,
    "target_min": 98.23,
    "target_std": 12.34
  },
  "data": [ {...}, {...} ]
}
```

**使用示例**:
- "查询 2025-08-30 18:00:00 到 19:00:00 的束流数据"
- "给我看 2025-08-31 02:00:00 到 03:00:00 的 target 和 feature1 两列，只要 10 条"

### 2. get_data_info
**功能**: 获取数据集的概要信息（总记录数、时间范围、列名、target 统计、样本记录）

**参数**:
- `include_target_stats` (可选): 是否返回 target 统计信息，默认 true
- `include_sample` (可选): 是否返回样本数据，默认 true
- `sample_size` (可选): 样本条数，范围 1-50，默认 3

**返回结构**:
```json
{
  "success": true,
  "tool": "get_data_info",
  "message": "数据集信息获取成功",
  "data_info": {
    "total_records": 1440,
    "columns": ["时间", "target", "feature1", ...],
    "time_range": { "start": "...", "end": "..." },
    "target_stats": { "mean": ..., "max": ..., "min": ..., "std": ... }
  },
  "sample": [ {...}, {...}, {...} ]
}
```

**使用示例**:
- "数据集有哪些列？时间范围是多少？"
- "给我看 5 条样本数据"

## 调用时机建议
- 首次使用时先调用 `get_data_info` 了解数据结构
- 在进行异常检测/诊断前，先用 `query_beam_data` 确认数据是否存在
- 用户明确要求查看数据或进行数据核实时调用

## 错误处理
- 时间格式不正确：返回清晰的错误提示和建议格式
- 时间段无数据：返回 success=true 但 message 提示无数据
- columns 中部分列不存在：返回可用列和被忽略的列
- limit 超出范围 (1-200)：返回错误并建议合法范围

## 依赖文件
- 数据文件：`D:\code\graduate\llm\data\束流.csv`
- 工具源码：`D:\code\graduate\llm\tools\data_query.py`
