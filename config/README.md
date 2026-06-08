# config — 项目配置

集中管理 API 密钥、模型名称、数据路径等全局配置。

## 文件说明

| 文件 | 说明 |
|------|------|
| `config.py` | `Config` 类，从环境变量或 `.env` 加载配置 |
| `__init__.py` | 导出 `Config` |

## 配置项

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `MODELSCOPE_API_KEY` | — | ModelScope API 密钥 |
| `MODELSCOPE_BASE_URL` | `https://api-inference.modelscope.cn/v1` | API 地址 |
| `MODELSCOPE_LLM_MODEL` | `Qwen/Qwen3-VL-30B-A3B-Instruct` | 对话模型 |
| `MODELSCOPE_EMBEDDING_MODEL` | `Qwen/Qwen3-Embedding-0.6B` | 向量化模型 |
| `LOCAL_EMBEDDING_MODEL_PATH` | `Qwen/Qwen3-Embedding-0.6B` | 本地 Embedding 路径 |

## 其他常量

- `DATA_FILE`：束流数据文件名（`束流.csv`）
- `MAX_CONVERSATION_HISTORY`：最大对话历史条数（20）
- `STREAM_OUTPUT`：是否默认流式输出

## 使用示例

```python
from config import Config

# LLM 配置
api_config = Config.get_api_config()
# {'api_key': '...', 'base_url': '...', 'model': '...'}

# Embedding 配置
emb_config = Config.get_embedding_config()
```

## 注意事项

- `.env` 文件放在项目根目录，已被 `.gitignore` 忽略
- 不要将 API 密钥提交到版本库
