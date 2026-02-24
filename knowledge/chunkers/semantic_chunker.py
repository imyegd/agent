"""语义分块器"""
import re
import numpy as np
from typing import List, Optional
from .base_chunker import BaseChunker


class SemanticChunker(BaseChunker):
    """
    基于语义相似度的文本分块器
    
    工作原理：
    1. 将文本按段落分割
    2. 计算相邻段落之间的向量相似度
    3. 当相似度低于阈值时，认为出现"语义断裂点"，在此处分块
    4. 当相似度高于阈值时，将段落合并到同一块中
    """
    
    def __init__(
        self, 
        embedder=None,
        similarity_threshold: float = 0.7,
        max_chunk_size: int = 800, 
        min_chunk_size: int = 100,
        use_simple_fallback: bool = True
    ):
        """
        初始化语义分块器
        
        Args:
            embedder: 向量化器，用于计算段落的语义向量（如果为 None，则降级为简单分割）
            similarity_threshold: 相似度阈值，低于此值则认为出现语义断裂点（0-1之间）
            max_chunk_size: 每个块的最大字符数
            min_chunk_size: 每个块的最小字符数
            use_simple_fallback: 当没有 embedder 时，是否降级为简单的段落分割
        """
        self.embedder = embedder
        self.similarity_threshold = similarity_threshold
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.use_simple_fallback = use_simple_fallback
    
    def chunk(self, text: str) -> List[str]:
        """
        基于语义相似度分割文本
        
        Args:
            text: 输入文本
            
        Returns:
            文本块列表
        """
        if not text or not text.strip():
            return []
        
        # 如果没有 embedder，降级为简单分割
        if self.embedder is None:
            if self.use_simple_fallback:
                return self._simple_chunk(text)
            else:
                raise ValueError("需要提供 embedder 才能进行语义分块")
        
        # 1. 按段落分割
        paragraphs = self._split_paragraphs(text)
        
        if not paragraphs:
            return []
        
        if len(paragraphs) == 1:
            # 只有一个段落，检查是否需要进一步分割
            if len(paragraphs[0]) > self.max_chunk_size:
                return self._split_long_paragraph(paragraphs[0])
            return paragraphs
        
        # 2. 对每个段落进行向量化
        try:
            paragraph_embeddings = self.embedder.embed(paragraphs)
        except Exception as e:
            print(f"[警告] 向量化失败: {e}，降级为简单分割")
            return self._simple_chunk(text)
        
        # 3. 计算相邻段落之间的相似度
        similarities = self._compute_similarities(paragraph_embeddings)
        
        # 4. 根据相似度阈值进行分块
        chunks = self._merge_by_similarity(paragraphs, similarities)
        
        return chunks
    
    def _split_paragraphs(self, text: str) -> List[str]:
        """将文本按段落分割"""
        # 按双换行符或多个换行符分割
        paragraphs = re.split(r'\n\s*\n+', text)
        
        # 过滤空段落
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        return paragraphs
    
    def _compute_similarities(self, embeddings: np.ndarray) -> List[float]:
        """
        计算相邻段落之间的余弦相似度
        
        Args:
            embeddings: 段落向量矩阵，shape (n_paragraphs, embedding_dim)
            
        Returns:
            相似度列表，similarities[i] 表示段落 i 和段落 i+1 的相似度
        """
        similarities = []
        
        for i in range(len(embeddings) - 1):
            vec1 = embeddings[i]
            vec2 = embeddings[i + 1]
            
            # 计算余弦相似度
            similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
            similarities.append(float(similarity))
        
        return similarities
    
    def _merge_by_similarity(self, paragraphs: List[str], similarities: List[float]) -> List[str]:
        """
        根据相似度阈值合并段落
        
        当相似度 < threshold 时，认为出现语义断裂点，在此处分块
        当相似度 >= threshold 时，将段落合并
        
        Args:
            paragraphs: 段落列表
            similarities: 相邻段落之间的相似度列表
            
        Returns:
            合并后的文本块列表
        """
        if not paragraphs:
            return []
        
        chunks = []
        current_chunk = paragraphs[0]
        
        for i, similarity in enumerate(similarities):
            next_para = paragraphs[i + 1]
            
            # 检查是否出现语义断裂点
            is_semantic_break = similarity < self.similarity_threshold
            
            # 检查大小限制
            would_exceed_max = len(current_chunk) + len(next_para) + 2 > self.max_chunk_size
            
            if is_semantic_break or would_exceed_max:
                # 出现语义断裂点或超过最大大小，保存当前块
                if len(current_chunk) >= self.min_chunk_size:
                    chunks.append(current_chunk)
                    current_chunk = next_para
                elif chunks and would_exceed_max:
                    # 当前块太小但会超过最大大小，单独保存
                    chunks.append(current_chunk)
                    current_chunk = next_para
                else:
                    # 当前块太小且不会超过最大大小，继续合并
                    current_chunk += "\n\n" + next_para
            else:
                # 相似度高，合并段落
                current_chunk += "\n\n" + next_para
        
        # 添加最后一个块
        if current_chunk:
            if len(current_chunk) >= self.min_chunk_size:
                chunks.append(current_chunk)
            elif chunks:
                # 最后一块太小，合并到前一块
                if len(chunks[-1]) + len(current_chunk) + 2 <= self.max_chunk_size:
                    chunks[-1] += "\n\n" + current_chunk
                else:
                    chunks.append(current_chunk)
            else:
                # 只有一块，即使很小也保留
                chunks.append(current_chunk)
        
        return chunks
    
    def _simple_chunk(self, text: str) -> List[str]:
        """
        简单的段落分割（降级方案）
        当没有 embedder 时使用
        """
        paragraphs = self._split_paragraphs(text)
        
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            if not para:
                continue
            
            # 如果当前块加上新段落不超过最大大小，就添加
            if len(current_chunk) + len(para) + 2 <= self.max_chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
            else:
                # 保存当前块（如果足够大）
                if len(current_chunk) >= self.min_chunk_size:
                    chunks.append(current_chunk)
                    current_chunk = para
                elif current_chunk:
                    # 当前块太小，与新段落合并
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
                
                # 如果单个段落太长，需要进一步分割
                if len(current_chunk) > self.max_chunk_size:
                    sentences = self._split_sentences(current_chunk)
                    temp_chunk = ""
                    
                    for sent in sentences:
                        if len(temp_chunk) + len(sent) <= self.max_chunk_size:
                            temp_chunk += sent
                        else:
                            if temp_chunk:
                                chunks.append(temp_chunk.strip())
                            temp_chunk = sent
                    
                    current_chunk = temp_chunk
        
        # 添加最后一个块
        if current_chunk and len(current_chunk) >= self.min_chunk_size:
            chunks.append(current_chunk)
        elif current_chunk and chunks:
            chunks[-1] += "\n\n" + current_chunk
        elif current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _split_long_paragraph(self, paragraph: str) -> List[str]:
        """分割过长的单个段落"""
        sentences = self._split_sentences(paragraph)
        chunks = []
        current_chunk = ""
        
        for sent in sentences:
            if len(current_chunk) + len(sent) <= self.max_chunk_size:
                current_chunk += sent
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sent
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks if chunks else [paragraph]
    
    def _split_sentences(self, text: str) -> List[str]:
        """
        将文本分割成句子
        
        Args:
            text: 输入文本
            
        Returns:
            句子列表
        """
        # 中文和英文句子分割
        sentence_endings = r'([。！？\.!?]+[\s\n]*)'
        sentences = re.split(sentence_endings, text)
        
        # 重新组合句子和标点
        result = []
        for i in range(0, len(sentences) - 1, 2):
            if i + 1 < len(sentences):
                result.append(sentences[i] + sentences[i + 1])
            else:
                result.append(sentences[i])
        
        if len(sentences) % 2 == 1:
            result.append(sentences[-1])
        
        return [s for s in result if s.strip()]

