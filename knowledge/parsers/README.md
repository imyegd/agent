# knowledge/parsers — 文档解析器

将 PDF、TXT 等原始文档解析为纯文本，供分块和索引使用。

## 支持的格式

| 类型 | 解析器 | 说明 |
|------|--------|------|
| TXT | `TxtParser` | 纯文本直接读取 |
| PDF | `PdfParser` | 基于 PyMuPDF 本地解析 |
| PDF (API) | `PdfParserApi` | 通过外部 API 解析 |

## 工厂方法

```python
from knowledge.parsers.parser_factory import ParserFactory

parser = ParserFactory.create_parser("pdf")
text = parser.parse("knowledge/data/papers/example.pdf")
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `base_parser.py` | 解析器抽象基类 |
| `txt_parser.py` | TXT 解析 |
| `pdf_parser.py` | PDF 本地解析 |
| `pdf_parser_api.py` | PDF API 解析 |
| `parser_factory.py` | 工厂入口 |

## 输出

解析结果可缓存到 `parser_output/` 目录，避免重复解析大文件。

## 依赖

```bash
pip install pymupdf
```
