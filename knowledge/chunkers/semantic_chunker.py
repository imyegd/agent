"""语义分块器"""
import re
from typing import List
from .base_chunker import BaseChunker


class SemanticChunker(BaseChunker):
    """基于语义的文本分块器，按段落、句子等语义单元分割"""
    
    def __init__(self, max_chunk_size: int = 800, min_chunk_size: int = 100):
        """
        初始化语义分块器
        
        Args:
            max_chunk_size: 每个块的最大字符数
            min_chunk_size: 每个块的最小字符数
        """
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
    
    def chunk(self, text: str) -> List[str]:
        """
        按语义单元分割文本
        
        Args:
            text: 输入文本
            
        Returns:
            文本块列表
        """
        if not text or not text.strip():
            return []
        
        # 首先按双换行符分割段落
        paragraphs = re.split(r'\n\s*\n', text)
        
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
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
                    # 按句子分割
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
            # 最后一个块太小，合并到前一个块
            chunks[-1] += "\n\n" + current_chunk
        elif current_chunk:
            # 只有一个块，即使很小也要保留
            chunks.append(current_chunk)
        
        return chunks
    
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

