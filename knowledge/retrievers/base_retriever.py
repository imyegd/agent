"""
检索器基类
"""
from typing import List, Tuple


class BaseRetriever:
    """检索器基类"""
    
    def _apply_parent_chunks(
        self,
        results: List[Tuple[str, float]],
        top_k: int
    ) -> List[Tuple[str, float]]:
        """
        若有 parent_chunk 元数据，将子块替换为父块并去重（同一父块保留最高分）。
        
        Args:
            results: [(doc_content, score), ...]，doc 为子块内容
            top_k: 返回数量
            
        Returns:
            [(content, score), ...]，content 为父块（若有）或子块，按分数降序
        """
        if not results:
            return []
        
        metadata_list = getattr(self, 'metadata_list', None)
        documents = getattr(self, 'documents', None)
        
        if not metadata_list or not documents or len(metadata_list) != len(documents):
            return results[:top_k]
        
        # 子块内容 -> 在 documents 中的索引（取第一个匹配）
        doc_to_idx = {}
        for idx, doc in enumerate(documents):
            if doc not in doc_to_idx:
                doc_to_idx[doc] = idx
        
        # 转为 (内容, 分数)，内容优先用 parent_chunk
        content_to_best_score = {}
        for doc, score in results:
            idx = doc_to_idx.get(doc)
            if idx is not None and idx < len(metadata_list):
                meta = metadata_list[idx]
                if isinstance(meta, dict) and meta.get('parent_chunk') is not None:
                    content = meta['parent_chunk']
                else:
                    content = doc
            else:
                content = doc
            
            if content not in content_to_best_score or score > content_to_best_score[content]:
                content_to_best_score[content] = score
        
        # 按分数降序，取 top_k
        sorted_items = sorted(
            content_to_best_score.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]
        
        return [(content, score) for content, score in sorted_items]
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        检索相关文档
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            
        Returns:
            [(document, score), ...]
        """
        raise NotImplementedError
    
    def get_statistics(self) -> dict:
        """
        获取检索器统计信息
        
        Returns:
            统计信息字典
        """
        return {
            'retriever_type': self.__class__.__name__,
            'document_count': getattr(self, 'documents', None) and len(self.documents) or 0
        }
