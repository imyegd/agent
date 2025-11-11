# 束流数据智能查询系统

基于大语言模型（LLM）的束流数据智能查询系统，支持自然语言交互和函数调用。

## 项目简介

本项目是研究生毕业设计的第二部分，旨在利用大模型的能力（如工具调用、知识增强），让用户能用自然语言与束流数据系统交互。

### 主要功能

- 🔍 **自然语言查询**：用户可以用自然语言描述查询需求，系统自动理解并执行
- 🛠️ **工具调用**：基于 Function Calling 技术，让 LLM 能够调用数据查询工具
- 📊 **数据分析**：自动提供查询结果的统计信息（均值、最大值、最小值等）
- 💬 **上下文对话**：支持多轮对话，可以追问和关联查询

### 技术栈

- **大模型**：Qwen/Qwen3-VL-30B-A3B-Instruct（通过 ModelScope API）
- **数据处理**：Pandas
- **API 调用**：OpenAI SDK
- **编程语言**：Python 3.8+

## 项目架构

```
llm/
├── config/                 # 配置模块
│   ├── __init__.py
│   └── config.py          # API密钥、模型配置等
├── tools/                  # 工具模块
│   ├── __init__.py
│   └── data_query.py      # 数据查询工具
├── agents/                 # 代理模块
│   ├── __init__.py
│   └── llm_agent.py       # LLM代理，支持函数调用
├── data/                   # 数据目录（可选）
├── main.py                 # 主程序入口（命令行交互）
├── example.py              # 使用示例
├── test.py                 # 原始测试文件
├── 束流.csv               # 束流数据文件
├── requirements.txt        # 项目依赖
└── README.md              # 项目说明
```

### 模块说明

#### 1. Config 模块 (`config/`)
- 管理 API 密钥、模型配置等
- 支持从环境变量读取配置

#### 2. Tools 模块 (`tools/`)
- `DataQueryTool`：数据查询工具类
- `query_beam_data`：根据时间范围查询数据
- `get_data_info`：获取数据集概要信息
- `TOOLS`：工具定义（OpenAI Function Calling 格式）

#### 3. Agents 模块 (`agents/`)
- `BeamDataAgent`：标准版代理
- `StreamingBeamDataAgent`：流式输出版代理
- 支持多轮对话和工具调用

## 安装与使用

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API 密钥

方式一：修改 `config/config.py` 文件中的 `API_KEY`

方式二：设置环境变量
```bash
export MODELSCOPE_API_KEY="your-api-key"
```

### 3. 运行主程序

```bash
python main.py
```

使用流式输出：
```bash
python main.py --stream
```

### 4. 运行示例

```bash
python example.py
```

## 使用示例

### 命令行交互

```
您: 查询2025年8月31日两点到三点的束流数据

助手: 根据您的要求，我查询了2025年8月31日凌晨2点到3点的束流数据。
查询结果如下：
- 时间范围：2025-08-31 02:00:00 至 2025-08-31 03:00:00
- 数据条数：3600 条
- target（束流强度）统计：
  * 平均值：0.3042
  * 最大值：0.3156
  * 最小值：0.2987
  * 标准差：0.0028

数据已成功获取。您还需要了解其他信息吗？
```

### 代码调用

```python
from agents import BeamDataAgent
from config import Config

# 初始化代理
config = Config.get_api_config()
agent = BeamDataAgent(
    api_key=config['api_key'],
    base_url=config['base_url'],
    model=config['model']
)

# 发起查询
response = agent.chat("查询2025年8月30日下午5点到6点的束流数据")
print(response)
```

### 直接调用工具

```python
from tools import query_beam_data, get_data_info

# 获取数据概要
info = get_data_info()
print(f"总记录数: {info['total_records']}")

# 查询特定时间范围
result = query_beam_data(
    start_time="2025-08-30 17:23:26",
    end_time="2025-08-30 17:23:35"
)
print(f"查询到 {result['count']} 条记录")
```

## 数据格式

CSV 文件格式：
- `时间`：时间戳（ISO 8601 格式，如 `2025-08-30T17:23:26`）
- `target`：束流强度或束位
- `feature1` ~ `feature35`：传感器数据（电压、电流等）

## 功能特点

### 1. 智能时间解析

系统能理解多种时间表达方式：
- "2025年8月31日两点到三点"
- "8月30日下午5点到6点"
- "2025-08-30 17:23:26到17:23:30"

### 2. 函数调用（Function Calling）

LLM 自动识别用户意图并调用相应的工具函数：
```
用户请求 → LLM 解析 → 调用工具函数 → 返回结果 → LLM 生成回复
```

### 3. 上下文感知

支持多轮对话，可以追问：
```
用户: 查询8月30日下午5点到6点的数据
助手: [返回查询结果]
用户: 这段时间的平均值是多少？
助手: [基于上一次查询结果回答]
```

### 4. 错误处理

系统能优雅地处理各种错误情况：
- 无效的时间格式
- 不存在的时间范围
- 数据文件缺失
- API 调用失败

## 扩展性

### 添加新工具

1. 在 `tools/data_query.py` 中定义新的工具函数
2. 在 `TOOLS` 列表中添加工具描述
3. 在 `TOOL_FUNCTIONS` 字典中注册函数

示例：
```python
def analyze_fluctuation(start_time: str, end_time: str) -> Dict[str, Any]:
    """分析波动原因"""
    # 实现逻辑
    pass

# 添加到 TOOLS
TOOLS.append({
    "type": "function",
    "function": {
        "name": "analyze_fluctuation",
        "description": "分析指定时间范围内束流数据的波动原因",
        "parameters": {...}
    }
})

# 注册函数
TOOL_FUNCTIONS["analyze_fluctuation"] = analyze_fluctuation
```

### 更换模型

修改 `config/config.py` 中的 `MODEL_NAME` 即可：
```python
MODEL_NAME = 'your-model-name'
```

## 未来规划

- [ ] 添加更多数据分析工具（波动分析、异常检测等）
- [ ] 集成知识库，提供领域知识增强
- [ ] 开发 Web 可视化界面（第三部分）
- [ ] 支持批量查询和导出
- [ ] 添加数据预测功能（第一部分集成）

## 常见问题

### Q: 如何处理中文文件名？
A: Windows 环境下可能存在编码问题，建议将数据文件放在项目根目录，使用相对路径。

### Q: API 调用失败怎么办？
A: 检查网络连接和 API 密钥是否正确，确认 ModelScope Token 有效。

### Q: 如何查看详细的调用日志？
A: 系统会自动打印工具调用信息，包括函数名、参数和返回结果。

### Q: 支持哪些时间格式？
A: 支持 ISO 8601 格式和自然语言描述，系统会自动解析。

## 联系方式

如有问题或建议，请联系项目维护者。

## 许可证

本项目仅供学习和研究使用。

