"""
向量化模块 - 支持多种 Embedding 方法
"""
from typing import List, Union
import numpy as np
from abc import ABC, abstractmethod
import os
import sys

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config.config import Config


class BaseEmbedder(ABC):
    """Embedding 基类"""
    
    @abstractmethod
    def embed(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        将文本转换为向量
        
        Args:
            texts: 单个文本或文本列表
            
        Returns:
            向量数组，shape为 (n_texts, embedding_dim)
        """
        pass


class SimpleEmbedder(BaseEmbedder):
    """简单的 TF-IDF Embedding（不需要额外API）"""
    
    def __init__(self, max_features: int = 1000):
        """
        初始化简单向量化器
        
        Args:
            max_features: 最大特征数
        """
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=(1, 2),  # 使用1-gram和2-gram
            min_df=1
        )
        self.fitted = False
    
    def fit(self, corpus: List[str]):
        """
        训练向量化器
        
        Args:
            corpus: 文本语料库
        """
        if not corpus:
            raise ValueError("语料库不能为空")
        self.vectorizer.fit(corpus)
        self.fitted = True
    
    def embed(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        将文本转换为 TF-IDF 向量
        
        Args:
            texts: 单个文本或文本列表
            
        Returns:
            TF-IDF 向量数组
        """
        if not self.fitted:
            raise RuntimeError("向量化器未训练，请先调用 fit() 方法")
        
        if isinstance(texts, str):
            texts = [texts]
        
        return self.vectorizer.transform(texts).toarray()


class APIEmbedder(BaseEmbedder):
    """使用 API 进行 Embedding（如 OpenAI, ModelScope）"""
    
    def __init__(
        self, 
        api_key: str = None,
        base_url: str = None, 
        model: str = None
    ):
        """
        初始化 API Embedder
        
        Args:
            api_key: API密钥 (默认从配置文件读取)
            base_url: API基础URL (默认从配置文件读取)
            model: Embedding模型名称 (默认从配置文件读取)
        """
        # 从配置文件获取默认值
        embedding_config = Config.get_embedding_config()
        
        self.api_key = api_key or embedding_config['api_key']
        self.base_url = base_url or embedding_config['base_url']
        self.model = model or embedding_config['model']
        
        if not self.api_key:
            raise ValueError(
                "未配置 API Key！\n"
                "请在 .env 文件中设置: MODELSCOPE_API_KEY=your-token-here"
            )
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        except ImportError:
            raise ImportError("需要安装 openai 包: pip install openai")
    
    def embed(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        调用 API 获取 embeddings
        
        Args:
            texts: 单个文本或文本列表
            
        Returns:
            Embedding 向量数组
        """
        if isinstance(texts, str):
            texts = [texts]
        
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts,
                encoding_format="float"
            )
            
            # 提取 embedding 向量
            embeddings = [item.embedding for item in response.data]
            return np.array(embeddings)
            
        except Exception as e:
            raise RuntimeError(f"API调用失败: {str(e)}")


class HybridEmbedder(BaseEmbedder):
    """混合 Embedder - 优先使用API，失败时降级到简单方法"""
    
    def __init__(
        self, 
        api_key: str = None, 
        base_url: str = None, 
        model: str = None
    ):
        """
        初始化混合 Embedder
        
        Args:
            api_key: API密钥（可选，默认从配置文件读取）
            base_url: API基础URL（可选，默认从配置文件读取）
            model: Embedding模型名称（可选，默认从配置文件读取）
        """
        self.api_embedder = None
        self.simple_embedder = SimpleEmbedder()
        
        # 尝试初始化 API Embedder（会自动从配置文件读取）
        try:
            self.api_embedder = APIEmbedder(api_key, base_url, model)
            print(f"使用 API Embedder (ModelScope) - 模型: {self.api_embedder.model}")
        except ValueError as e:
            print(f"API 配置不完整: {e}")
            print("将使用简单 TF-IDF 方法")
        except Exception as e:
            print(f"API Embedder 初始化失败: {e}")
            print("将使用简单 TF-IDF 方法")
    
    def fit(self, corpus: List[str]):
        """训练简单向量化器（API方法不需要训练）"""
        self.simple_embedder.fit(corpus)
    
    def embed(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        尝试使用API，失败则降级到简单方法
        
        Args:
            texts: 单个文本或文本列表
            
        Returns:
            Embedding 向量数组
        """
        if self.api_embedder:
            try:
                return self.api_embedder.embed(texts)
            except Exception as e:
                print(f"API调用失败，降级到TF-IDF方法: {e}")
        
        return self.simple_embedder.embed(texts)


def create_embedder(method: str = "simple", **kwargs) -> BaseEmbedder:
    """
    工厂函数：创建指定类型的Embedder
    
    Args:
        method: 方法类型，可选 "simple", "api", "hybrid"
        **kwargs: 传递给Embedder的参数
        
    Returns:
        Embedder实例
    """
    if method == "simple":
        return SimpleEmbedder(**kwargs)
    elif method == "api":
        return APIEmbedder(**kwargs)
    elif method == "hybrid":
        return HybridEmbedder(**kwargs)
    else:
        raise ValueError(f"未知的方法类型: {method}")

