# 束流数据智能分析系统 - Web 前端

## 项目概述

这是一个基于 Flask + HTML/CSS/JavaScript 的单页面应用，提供束流数据智能分析的可视化界面。

## 功能特性

### 1. 智能对话 💬
- 支持自然语言与系统交互
- 自动调用后端工具（数据查询、波动分析、知识库等）
- 实时流式对话体验

**示例对话：**
- "查询2025年8月31日两点到三点的束流数据"
- "分析8月30日下午的波动情况"
- "feature1是什么意思？"

### 2. 波动分析 📊
- 选择时间范围进行 PLS 波动分析
- 快速选择时间段（1小时/6小时/1天/7天）
- 生成可视化图表（T² 和 SPE 统计量）
- 结合知识库提供异常解释和解决方案

### 3. 知识库搜索 📚
- 搜索特征物理含义
- 查询故障解决方案
- 浏览领域概念
- 按类型筛选（特征/解决方案/概念）

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动 Web 服务

```bash
python app.py
```

服务将在 `http://localhost:5000` 启动。

### 3. 访问界面

在浏览器中打开：
```
http://localhost:5000
```

## 项目结构

```
llm/
├── app.py                      # Flask 后端服务
├── templates/
│   └── index.html              # HTML 模板
├── static/
│   ├── css/
│   │   └── style.css          # 样式文件
│   └── js/
│       └── main.js            # 前端交互逻辑
├── agents/                     # Agent 模块
├── tools/                      # 工具模块
├── knowledge/                  # 知识库模块
├── models/                     # 机器学习模型
├── data/                       # 数据文件
└── output/                     # 输出文件（图表等）
```

## API 接口

### 1. 聊天接口
```
POST /api/chat
Body: { "message": "查询2025年8月31日的数据" }
```

### 2. 波动分析
```
POST /api/analyze
Body: { "start_time": "2025-08-30 14:00:00", "end_time": "2025-08-30 18:00:00" }
```

### 3. 可视化接口
```
POST /api/visualize
Body: { "start_time": "2025-08-30 14:00:00", "end_time": "2025-08-30 18:00:00" }
```

### 4. 知识库搜索
```
POST /api/knowledge/search
Body: { "query": "feature1", "top_k": 3, "doc_type": "feature" }
```

### 5. 数据集信息
```
GET /api/data/info
```

### 6. 重置对话
```
POST /api/reset
```

## 界面预览

### 智能对话界面
- 深色科技风格
- 实时对话体验
- 支持 Markdown 渲染
- 自动滚动和换行

### 波动分析界面
- 左侧控制面板：时间选择、快速范围
- 右侧结果面板：文本报告 + 可视化图表
- 支持一键分析

### 知识库界面
- 搜索框 + 类型筛选
- 结果按相关度排序
- 高亮显示关键信息

## 技术栈

- **后端**: Flask 3.0+
- **前端**: HTML5 + CSS3 + JavaScript (原生)
- **图标**: Font Awesome 6.4
- **通信**: RESTful API + CORS

## 配置说明

### API 配置
在 `config/api_config.yaml` 中配置 OpenAI API：

```yaml
api_key: "your-api-key"
base_url: "https://api.openai.com/v1"
model: "gpt-4o-mini"
```

### 数据路径
在 `config/paths.yaml` 中配置数据路径：

```yaml
data_file: "data/束流.csv"
model_file: "models/pls_model.pkl"
output_dir: "output"
```

## 注意事项

1. 确保已训练 PLS 模型（`models/pls_model.pkl`）
2. 确保数据文件存在（`data/束流.csv`）
3. 需要有效的 OpenAI API Key
4. 首次运行会自动创建 `output` 目录

## 故障排查

### 1. 端口占用
如果 5000 端口被占用，修改 `app.py` 中的端口：
```python
app.run(debug=True, host='0.0.0.0', port=8080)
```

### 2. CORS 错误
已配置 `flask-cors`，如果仍有问题，检查浏览器控制台。

### 3. API 调用失败
检查：
- API Key 是否正确
- 网络连接是否正常
- Base URL 是否有效

### 4. 图表不显示
检查：
- `output` 目录是否存在
- matplotlib 是否正确安装
- 时间范围内是否有数据

## 后续优化方向

1. **用户体验**
   - 添加图表交互功能（缩放、筛选）
   - 支持多种图表类型
   - 添加数据导出功能

2. **功能扩展**
   - 实时数据监控
   - 告警推送
   - 历史分析记录

3. **性能优化**
   - 添加数据缓存
   - 异步加载
   - WebSocket 实时通信

4. **安全性**
   - 用户认证
   - API 限流
   - 数据加密

## 开发团队

束流数据智能分析系统 v1.0

