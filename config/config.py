"""
配置文件
存储API密钥、模型配置等信息
"""

import os


class Config:
    """配置类"""
    
    # ModelScope API配置
    API_KEY = os.getenv('MODELSCOPE_API_KEY', 'ms-da777fdb-1e63-4cb2-bf5d-9ec15d4c0355')
    BASE_URL = 'https://api-inference.modelscope.cn/v1'
    MODEL_NAME = 'Qwen/Qwen3-VL-30B-A3B-Instruct'
    
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
        return config
    
    @classmethod
    def get_api_config(cls):
        """获取API配置"""
        return {
            'api_key': cls.API_KEY,
            'base_url': cls.BASE_URL,
            'model': cls.MODEL_NAME
        }


# 创建默认配置实例
default_config = Config()

