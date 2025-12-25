"""
配置文件
存储API密钥、模型配置等信息
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)


class Config:
    """配置类"""
    
    # ModelScope API配置
    API_KEY = os.getenv('MODELSCOPE_API_KEY', '')
    BASE_URL = os.getenv('MODELSCOPE_BASE_URL', 'https://api-inference.modelscope.cn/v1')
    
    # LLM 模型配置
    MODEL_NAME = os.getenv('MODELSCOPE_LLM_MODEL', 'Qwen/Qwen3-VL-30B-A3B-Instruct')
    
    # Embedding 模型配置
    EMBEDDING_MODEL = os.getenv('MODELSCOPE_EMBEDDING_MODEL', 'Qwen/Qwen3-Embedding-0.6B')
    
    # 数据文件配置
    DATA_FILE = '束流.csv'  # 相对于项目根目录
    
    # 其他配置
    MAX_CONVERSATION_HISTORY = 20  # 最大对话历史条数
    STREAM_OUTPUT = False  # 是否使用流式输出
    
    @classmethod
    def from_env(cls):
        """从环境变量加载配置"""
        config = cls()
        config.API_KEY = os.getenv('MODELSCOPE_API_KEY', config.API_KEY)
        config.BASE_URL = os.getenv('MODELSCOPE_BASE_URL', config.BASE_URL)
        config.MODEL_NAME = os.getenv('MODELSCOPE_LLM_MODEL', config.MODEL_NAME)
        config.EMBEDDING_MODEL = os.getenv('MODELSCOPE_EMBEDDING_MODEL', config.EMBEDDING_MODEL)
        return config
    
    @classmethod
    def get_api_config(cls):
        """获取 LLM API 配置"""
        return {
            'api_key': cls.API_KEY,
            'base_url': cls.BASE_URL,
            'model': cls.MODEL_NAME
        }
    
    @classmethod
    def get_embedding_config(cls):
        """获取 Embedding API 配置"""
        return {
            'api_key': cls.API_KEY,
            'base_url': cls.BASE_URL,
            'model': cls.EMBEDDING_MODEL
        }


# 创建默认配置实例
default_config = Config()

