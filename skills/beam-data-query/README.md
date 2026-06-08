# beam-data-query — 束流数据查询技能

按时间范围查询束流 CSV 数据，获取数据集元信息。

## 包含工具

| 工具 | 说明 |
|------|------|
| `query_beam_data` | 按时间范围查询，支持列筛选和统计摘要 |
| `get_data_info` | 获取记录数、时间范围、列名等元信息 |

## 实现

- 代码：[tools/data_query.py](../../tools/data_query.py)
- 数据：[data/束流.csv](../../data/束流.csv)

## 详细文档

完整参数、返回结构和调用示例见 [SKILL.md](SKILL.md)。

## 典型调用顺序

```
get_data_info → query_beam_data
```
