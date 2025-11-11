# 项目架构说明

## 整体架构

本项目采用模块化设计，将功能划分为配置、工具、代理三个核心模块。

```
┌─────────────────────────────────────────────────────────┐
│                      用户层                             │
│  (命令行交互 / Python API / Web界面-未来)               │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│                    代理层 (agents/)                     │
│  ┌──────────────────────────────────────────────────┐  │
│  │          BeamDataAgent / StreamingAgent          │  │
│  │  - 对话管理                                       │  │
│  │  - 意图理解                                       │  │
│  │  - 工具调用                                       │  │
│  │  - 响应生成                                       │  │
│  └─────────────┬────────────────────────────────────┘  │
└────────────────┼────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│                   LLM 服务                              │
│         (Qwen3-VL-30B via ModelScope API)              │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│                   工具层 (tools/)                       │
│  ┌──────────────────────────────────────────────────┐  │
│  │            Data Query Tool                        │  │
│  │  - query_beam_data()  : 时间范围查询             │  │
│  │  - get_data_info()    : 数据概要查询             │  │
│  │  - [可扩展更多工具]                               │  │
│  └─────────────┬────────────────────────────────────┘  │
└────────────────┼────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│                  数据层                                 │
│              束流.csv (36,000+ 记录)                    │
│  - 时间 (timestamp)                                     │
│  - target (束流强度/束位)                               │
│  - feature1-35 (传感器数据)                            │
└─────────────────────────────────────────────────────────┘
```

## 核心模块详解

### 1. Config 模块 (`config/`)

**职责**：管理系统配置

**文件结构**：
```
config/
├── __init__.py          # 模块导出
└── config.py            # 配置类定义
```

**核心类**：
- `Config`: 配置类
  - `API_KEY`: ModelScope API密钥
  - `BASE_URL`: API基础URL
  - `MODEL_NAME`: 模型名称
  - `DATA_FILE`: 数据文件路径

**使用示例**：
```python
from config import Config
config = Config.get_api_config()
```

### 2. Tools 模块 (`tools/`)

**职责**：提供数据查询和分析工具

**文件结构**：
```
tools/
├── __init__.py          # 模块导出
└── data_query.py        # 数据查询工具
```

**核心组件**：

#### DataQueryTool 类
- `_load_data()`: 加载CSV数据
- `query_by_time_range()`: 时间范围查询
- `get_data_summary()`: 获取数据概要

#### 工具函数（供LLM调用）
- `query_beam_data()`: 查询束流数据
- `get_data_info()`: 获取数据信息

#### 工具定义
- `TOOLS`: OpenAI Function Calling 格式的工具描述
- `TOOL_FUNCTIONS`: 工具函数映射表

**工具定义格式**：
```json
{
  "type": "function",
  "function": {
    "name": "query_beam_data",
    "description": "查询指定时间范围内的束流数据...",
    "parameters": {
      "type": "object",
      "properties": {
        "start_time": {...},
        "end_time": {...},
        "columns": {...}
      },
      "required": ["start_time", "end_time"]
    }
  }
}
```

### 3. Agents 模块 (`agents/`)

**职责**：实现与LLM的交互和工具调用

**文件结构**：
```
agents/
├── __init__.py          # 模块导出
└── llm_agent.py         # LLM代理实现
```

**核心类**：

#### BeamDataAgent
标准版代理，提供完整的对话功能。

**主要方法**：
- `__init__()`: 初始化代理（API配置、系统提示等）
- `chat()`: 处理用户输入，返回完整响应
- `_call_llm()`: 调用LLM
- `_execute_tool_call()`: 执行工具调用
- `reset_conversation()`: 重置对话历史

**工作流程**：
```
用户输入
  ↓
添加到对话历史
  ↓
调用LLM（带工具定义）
  ↓
LLM返回响应
  ├─→ 文本响应 → 返回给用户
  └─→ 工具调用请求
       ↓
     执行工具函数
       ↓
     将结果添加到对话历史
       ↓
     再次调用LLM
       ↓
     返回最终响应
```

#### StreamingBeamDataAgent
流式输出版代理，继承自 `BeamDataAgent`。

**特点**：
- 实时输出响应内容（逐字符）
- 改善用户体验（减少等待感）
- 支持工具调用

**主要方法**：
- `chat_stream()`: 流式处理用户输入

### 4. 入口模块

#### main.py
**职责**：命令行交互界面

**功能**：
- 欢迎界面和帮助信息
- 交互式对话循环
- 命令处理（exit, reset, help）
- 错误处理和友好提示

**两种模式**：
- `main()`: 标准模式
- `main_stream()`: 流式输出模式

**使用方式**：
```bash
python main.py          # 标准模式
python main.py --stream # 流式模式
```

#### example.py
**职责**：提供完整的使用示例

**包含示例**：
1. 直接调用工具函数
2. 使用代理进行自然语言交互
3. 错误处理演示

#### quick_start.py
**职责**：快速测试系统功能

**测试项**：
1. 数据加载和概要查询
2. 时间范围查询
3. 工具定义检查

## 数据流

### 查询数据流

```
用户: "查询2025年8月30日下午5点到6点的数据"
  ↓
main.py: 接收输入
  ↓
BeamDataAgent.chat(): 处理输入
  ↓
LLM (Qwen3): 理解意图
  ↓
返回工具调用: query_beam_data(
  start_time="2025-08-30 17:00:00",
  end_time="2025-08-30 18:00:00"
)
  ↓
执行工具: DataQueryTool.query_by_time_range()
  ↓
Pandas: 查询 CSV 数据
  ↓
返回结果: {success, count, data, statistics}
  ↓
LLM: 基于结果生成回复
  ↓
用户看到: "查询到 3600 条记录，target平均值为..."
```

## 扩展点

### 1. 添加新工具

在 `tools/data_query.py` 中：

```python
# 1. 定义工具函数
def analyze_fluctuation(start_time: str, end_time: str) -> Dict:
    """分析波动"""
    # 实现逻辑
    pass

# 2. 添加工具描述
TOOLS.append({
    "type": "function",
    "function": {
        "name": "analyze_fluctuation",
        "description": "分析束流波动原因",
        "parameters": {...}
    }
})

# 3. 注册函数
TOOL_FUNCTIONS["analyze_fluctuation"] = analyze_fluctuation
```

### 2. 更换/添加数据源

修改 `DataQueryTool` 类：

```python
class DataQueryTool:
    def __init__(self, data_path: str):
        self.data_path = data_path
        # 可以添加数据库连接等
        self.db_conn = connect_to_db()
    
    def query_by_time_range(self, ...):
        # 可以从数据库查询而不是CSV
        pass
```

### 3. 集成Web界面

创建 `app.py`（第三部分）：

```python
from flask import Flask, request, jsonify
from agents import BeamDataAgent

app = Flask(__name__)
agent = BeamDataAgent(...)

@app.route('/api/chat', methods=['POST'])
def chat():
    user_input = request.json['message']
    response = agent.chat(user_input)
    return jsonify({'response': response})
```

### 4. 添加知识库

在代理的系统提示中集成领域知识：

```python
self.system_prompt = """
你是束流数据分析助手...

【领域知识】
- 束流强度的正常范围：0.2-0.5
- target值突然下降可能原因：...
- feature1代表：电压传感器1
...
"""
```

### 5. 集成第一部分（机器学习模型）

```python
# 在 tools/ 中添加
def predict_beam_intensity(features: List[float]) -> float:
    """使用训练好的模型预测"""
    model = load_model('model.pkl')
    return model.predict([features])[0]

# 添加到 TOOLS
TOOLS.append({...})
```

## 技术选型说明

### 为什么选择 OpenAI SDK？
- 统一的接口标准
- 支持 Function Calling
- ModelScope API 兼容 OpenAI 格式

### 为什么选择 Pandas？
- 高效的数据处理能力
- 强大的时间序列支持
- 丰富的统计功能

### 为什么选择 Qwen3-VL？
- 支持 Function Calling
- 中文理解能力强
- 通过 ModelScope 免费使用

## 性能考虑

### 数据加载
- **当前**：每次创建 `DataQueryTool` 时加载整个CSV
- **优化**：使用单例模式，只加载一次
- **扩展**：使用数据库存储，按需查询

### LLM调用
- **当前**：每次对话都调用API
- **优化**：缓存常见查询结果
- **扩展**：本地部署模型

### 对话历史
- **当前**：存储在内存中
- **扩展**：持久化到数据库
- **优化**：限制历史长度，只保留最近N轮

## 安全考虑

1. **API密钥管理**
   - 不要在代码中硬编码
   - 使用环境变量
   - 添加到 .gitignore

2. **输入验证**
   - 验证时间格式
   - 检查查询范围
   - 防止SQL注入（如果使用数据库）

3. **错误处理**
   - 捕获所有异常
   - 不暴露敏感信息
   - 友好的错误提示

## 测试策略

### 单元测试（建议添加）
```python
# tests/test_data_query.py
def test_query_by_time_range():
    tool = DataQueryTool()
    result = tool.query_by_time_range(
        "2025-08-30 17:23:26",
        "2025-08-30 17:23:30"
    )
    assert result['success'] == True
    assert result['count'] > 0
```

### 集成测试
- `quick_start.py`: 基础功能测试
- `example.py`: 完整流程测试

### 端到端测试（建议添加）
```python
def test_end_to_end():
    agent = BeamDataAgent(...)
    response = agent.chat("查询数据")
    assert "成功" in response or "条记录" in response
```

## 部署建议

### 开发环境
```bash
pip install -r requirements.txt
python main.py
```

### 生产环境
1. 使用虚拟环境
2. 配置环境变量
3. 使用日志系统
4. 添加监控
5. 容器化部署（Docker）

```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

## 未来架构演进

```
当前 (v1.0): CLI + 数据查询
  ↓
v1.1: + Web界面 + 更多分析工具
  ↓
v1.2: + 机器学习预测集成
  ↓
v2.0: + 知识库 + 多模态支持
  ↓
v3.0: 完整的智能分析平台
```

