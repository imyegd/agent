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
    """简单的 TF-IDF Embedding（使用 jieba 中文分词）"""
    
    def __init__(self, max_features: int = 1000):
        """
        初始化简单向量化器
        
        Args:
            max_features: 最大特征数
        """
        from sklearn.feature_extraction.text import TfidfVectorizer
        import jieba
        self.jieba = jieba
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=(1, 2),  # 使用1-gram和2-gram
            min_df=1,
            analyzer='word',  # 使用词级别分析
            token_pattern=r"(?u)\b\w+\b"  # 匹配中文字符
        )
        self.fitted = False
    
    def _segment(self, text: str) -> str:
        """
        使用 jieba 对文本进行分词
        
        Args:
            text: 原始文本
            
        Returns:
            分词后的文本（空格分隔）
        """
        words = self.jieba.cut(text)
        words = [w.strip() for w in words if len(w.strip()) > 0]
        return ' '.join(words)
    
    def fit(self, corpus: List[str]):
        """
        训练向量化器
        
        Args:
            corpus: 文本语料库
        """
        if not corpus:
            raise ValueError("语料库不能为空")
        # 对语料库进行分词
        segmented_corpus = [self._segment(doc) for doc in corpus]
        self.vectorizer.fit(segmented_corpus)
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
        
        # 对文本进行分词
        segmented_texts = [self._segment(text) for text in texts]
        
        return self.vectorizer.transform(segmented_texts).toarray()


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


class LocalModelEmbedder(BaseEmbedder):
    """使用本地加载的 Transformers 模型进行 Embedding"""
    
    def __init__(
        self,
        model_path: str = None,
        device: str = "cpu",
        batch_size: int = 32,
        max_length: int = 512
    ):
        """
        初始化本地模型 Embedder
        
        Args:
            model_path: 本地模型路径或 HuggingFace 模型名称 (默认从配置文件读取)
            device: 设备类型，"cpu" 或 "cuda"
            batch_size: 批处理大小
            max_length: 最大文本长度
        """
        # 从配置文件获取默认值
        local_config = Config.get_local_embedding_config()
        self.model_path = model_path or local_config['model_path']
        self.device = device
        self.batch_size = batch_size
        self.max_length = max_length
        
        print(f"正在加载本地模型: {self.model_path}")
        
        try:
            from transformers import AutoTokenizer, AutoModel
            import torch
            
            self.torch = torch
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path, trust_remote_code=True)
            self.model = AutoModel.from_pretrained(self.model_path, trust_remote_code=True)
            
            # 将模型移到指定设备
            if device == "cuda" and torch.cuda.is_available():
                self.model = self.model.to("cuda")
                print(f"模型已加载到 GPU: {torch.cuda.get_device_name(0)}")
            else:
                self.model = self.model.to("cpu")
                print(f"模型已加载到 CPU")
            
            self.model.eval()  # 设置为评估模式
            print(f"本地模型加载成功！")
            
        except ImportError:
            raise ImportError(
                "需要安装 transformers 和 torch 包:\n"
                "pip install transformers torch"
            )
        except Exception as e:
            raise RuntimeError(f"本地模型加载失败: {str(e)}")
    
    def _mean_pooling(self, model_output, attention_mask):
        """均值池化"""
        token_embeddings = model_output[0]
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return self.torch.sum(token_embeddings * input_mask_expanded, 1) / self.torch.clamp(
            input_mask_expanded.sum(1), min=1e-9
        )
    
    def embed(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        使用本地模型获取 embeddings
        
        Args:
            texts: 单个文本或文本列表
            
        Returns:
            Embedding 向量数组
        """
        if isinstance(texts, str):
            texts = [texts]
        
        all_embeddings = []
        
        try:
            with self.torch.no_grad():
                # 分批处理
                for i in range(0, len(texts), self.batch_size):
                    batch_texts = texts[i:i + self.batch_size]
                    
                    # Tokenize
                    encoded_input = self.tokenizer(
                        batch_texts,
                        padding=True,
                        truncation=True,
                        max_length=self.max_length,
                        return_tensors='pt'
                    )
                    
                    # 移到指定设备
                    encoded_input = {k: v.to(self.device) for k, v in encoded_input.items()}
                    
                    # 获取模型输出
                    model_output = self.model(**encoded_input)
                    
                    # 均值池化
                    batch_embeddings = self._mean_pooling(
                        model_output,
                        encoded_input['attention_mask']
                    )
                    
                    # 归一化
                    batch_embeddings = self.torch.nn.functional.normalize(
                        batch_embeddings,
                        p=2,
                        dim=1
                    )
                    
                    # 转为 numpy
                    all_embeddings.append(batch_embeddings.cpu().numpy())
            
            return np.vstack(all_embeddings)
            
        except Exception as e:
            raise RuntimeError(f"本地模型推理失败: {str(e)}")


def create_embedder(method: str = "api", **kwargs) -> BaseEmbedder:
    """
    工厂函数：创建指定类型的Embedder
    
    Args:
        method: 方法类型，可选 "simple", "api", "local"
        **kwargs: 传递给Embedder的参数
        
    Returns:
        Embedder实例
    """
    if method == "simple":
        return SimpleEmbedder(**kwargs)
    elif method == "api":
        return APIEmbedder(**kwargs)
    elif method == "local":
        return LocalModelEmbedder(**kwargs)
    else:
        raise ValueError(f"未知的方法类型: {method}。支持: 'simple', 'api', 'local'")

