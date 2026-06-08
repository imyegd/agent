# knowledge/chunkers — 文本分块器

将解析后的文档切分为适合向量检索的文本块（chunk）。

## 分块策略

| 类型 | 类名 | 说明 |
|------|------|------|
| `fixed` | `FixedSizeChunker` | 固定字符数分块，速度快 |
| `semantic` | `SemanticChunker` | 按语义段落分块，保留完整性 |
| `chapter` | `ChapterChunker` | 按章节标题分块 |
| `parent_child` | `ParentChildChunker` | 父子双层索引，检索用小块、返回用大块 |

## 工厂方法

```python
from knowledge.chunkers.chunker_factory import ChunkerFactory

chunker = ChunkerFactory.create_chunker(
    chunker_type="semantic",
    chunk_size=500,
    chunk_overlap=50
)
chunks = chunker.chunk(text)
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `base_chunker.py` | 分块器抽象基类 |
| `fixed_size_chunker.py` | 固定大小分块 |
| `semantic_chunker.py` | 语义分块 |
| `chapter_chunker.py` | 章节分块 |
| `parent_child_chunker.py` | 父子分块 |
| `chunker_factory.py` | 工厂入口 |

## 输出

分块结果可写入 `chunker_output/`（开发调试用），最终索引由 `vector_store/` 管理。

## 实验对比

不同策略的检索效果对比见 [experiment/](../../experiment/README.md)。
