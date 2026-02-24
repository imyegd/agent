"""章节分块器"""
import re
from typing import List, Tuple
from .base_chunker import BaseChunker


class ChapterChunker(BaseChunker):
    """基于章节结构的文本分块器，按 Markdown 标题层级分割"""
    
    def __init__(
        self, 
        max_level: int = 3,
        min_chunk_size: int = 50,
        include_title_in_chunk: bool = True
    ):
        """
        初始化章节分块器
        
        Args:
            max_level: 最大章节层级 (1=#, 2=##, 3=###)，超过此层级的标题不作为分割点
            min_chunk_size: 最小块大小（字符数），小于此大小的块会尝试与相邻块合并
            include_title_in_chunk: 是否将章节标题包含在块内容中
        """
        self.max_level = max_level
        self.min_chunk_size = min_chunk_size
        self.include_title_in_chunk = include_title_in_chunk
    
    def chunk(self, text: str) -> List[str]:
        """
        按章节结构分割文本
        
        Args:
            text: 输入文本
            
        Returns:
            文本块列表
        """
        if not text or not text.strip():
            return []
        
        # 1. 提取所有章节标题及其位置
        sections = self._extract_sections(text)
        
        if not sections:
            # 如果没有检测到章节，返回整个文本
            return [text.strip()] if text.strip() else []
        
        # 2. 根据章节划分文本块
        chunks = []
        for i, (level, title, start_pos, end_pos) in enumerate(sections):
            # 提取章节内容
            content = text[start_pos:end_pos].strip()
            
            if not content:
                continue
            
            # 如果不包含标题，则去掉标题行
            if not self.include_title_in_chunk and title:
                # 找到标题行的结束位置
                title_end = content.find('\n')
                if title_end != -1:
                    content = content[title_end + 1:].strip()
            
            if content:
                chunks.append(content)
        
        # 3. 合并过小的块
        chunks = self._merge_small_chunks(chunks)
        
        return chunks
    
    def _extract_sections(self, text: str) -> List[Tuple[int, str, int, int]]:
        """
        提取文本中的所有章节标题及其位置
        
        Args:
            text: 输入文本
            
        Returns:
            [(章节层级, 标题文本, 开始位置, 结束位置), ...]
        """
        # 匹配 Markdown 标题：行首的 # 号
        # 支持 #, ##, ###, ####, #####, ###### 以及中间可能有空格
        pattern = r'^(#{1,6})\s+(.+?)$'
        
        sections = []
        lines = text.split('\n')
        current_pos = 0
        
        for i, line in enumerate(lines):
            match = re.match(pattern, line.strip())
            if match:
                level = len(match.group(1))  # # 的数量
                title = match.group(2).strip()
                
                # 只处理不超过 max_level 的标题
                if level <= self.max_level:
                    sections.append((level, title, current_pos, -1))
                    
                    # 更新上一个章节的结束位置
                    if len(sections) > 1:
                        sections[-2] = (
                            sections[-2][0],
                            sections[-2][1],
                            sections[-2][2],
                            current_pos
                        )
            
            current_pos += len(line) + 1  # +1 for newline
        
        # 设置最后一个章节的结束位置
        if sections:
            sections[-1] = (
                sections[-1][0],
                sections[-1][1],
                sections[-1][2],
                len(text)
            )
        
        return sections
    
    def _merge_small_chunks(self, chunks: List[str]) -> List[str]:
        """
        合并过小的文本块
        
        Args:
            chunks: 原始文本块列表
            
        Returns:
            合并后的文本块列表
        """
        if not chunks:
            return []
        
        merged = []
        current_chunk = chunks[0]
        
        for i in range(1, len(chunks)):
            if len(current_chunk) < self.min_chunk_size:
                # 当前块太小，与下一块合并
                current_chunk += "\n\n" + chunks[i]
            else:
                # 当前块足够大，保存并开始新块
                merged.append(current_chunk)
                current_chunk = chunks[i]
        
        # 添加最后一个块
        if current_chunk:
            if merged and len(current_chunk) < self.min_chunk_size:
                # 最后一块太小，合并到前一块
                merged[-1] += "\n\n" + current_chunk
            else:
                merged.append(current_chunk)
        
        return merged
    
    def get_chapter_structure(self, text: str) -> List[Tuple[int, str]]:
        """
        获取文本的章节结构（用于调试和预览）
        
        Args:
            text: 输入文本
            
        Returns:
            [(章节层级, 标题文本), ...]
        """
        sections = self._extract_sections(text)
        return [(level, title) for level, title, _, _ in sections]


if __name__ == "__main__":
    # 测试代码
    test_text = """
# 第一章 引言

这是引言的内容。包含一些基本介绍。

# 第二章 方法

## 2.1 数据集

这是数据集的描述。

## 2.2 模型架构

### 2.2.1 编码器

编码器的详细说明。

### 2.2.2 解码器

解码器的详细说明。

# 第三章 实验

实验部分的内容。

## 3.1 实验设置

实验设置的详细说明。

# 第四章 结论

这是结论部分。
"""
    
    print("=" * 60)
    print("测试章节分块器")
    print("=" * 60)
    
    # 测试不同的 max_level
    for max_level in [1, 2, 3]:
        print(f"\n[测试] max_level={max_level}")
        chunker = ChapterChunker(max_level=max_level, min_chunk_size=20)
        
        # 显示章节结构
        structure = chunker.get_chapter_structure(test_text)
        print(f"检测到的章节结构:")
        for level, title in structure:
            indent = "  " * (level - 1)
            print(f"  {indent}{'#' * level} {title}")
        
        # 分块
        chunks = chunker.chunk(test_text)
        print(f"\n分块结果: {len(chunks)} 个块")
        for i, chunk in enumerate(chunks, 1):
            preview = chunk[:80].replace('\n', ' ')
            print(f"  块 {i}: {preview}... (长度: {len(chunk)})")
