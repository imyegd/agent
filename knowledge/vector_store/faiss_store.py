"""FAISS向量存储"""
import numpy as np
import pickle
import os
from typing import List, Tuple, Optional


class FaissVectorStore:
    """FAISS向量存储和检索"""
    
    def __init__(self, dimension: Optional[int] = None):
        """
        初始化FAISS向量存储
        
        Args:
            dimension: 向量维度，如果要创建新索引则必需
        """
        self.dimension = dimension
        self.index = None
        self.documents = []
        
        if dimension is not None:
            self._create_index(dimension)
    
    def _create_index(self, dimension: int):
        """创建FAISS索引"""
        try:
            import faiss
            self.faiss = faiss
        except ImportError:
            raise ImportError("需要安装 faiss: pip install faiss-cpu 或 faiss-gpu")
        
        # 使用 IndexFlatL2 进行精确搜索
        self.index = self.faiss.IndexFlatL2(dimension)
        print(f"创建FAISS索引，维度: {dimension}")
    
    def add_documents(self, embeddings: np.ndarray, documents: List[str]):
        """
        添加文档和对应的向量到索引
        
        Args:
            embeddings: 文档向量，shape (n, dimension)
            documents: 文档文本列表
        """
        if self.index is None:
            self._create_index(embeddings.shape[1])
        
        if embeddings.shape[0] != len(documents):
            raise ValueError("向量数量和文档数量不匹配")
        
        # 确保是float32类型
        embeddings = embeddings.astype('float32')
        
        # 添加到索引
        self.index.add(embeddings)
        self.documents.extend(documents)
        
        print(f"添加 {len(documents)} 个文档到索引，当前总数: {len(self.documents)}")
    
    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        搜索最相似的文档
        
        Args:
            query_embedding: 查询向量，shape (1, dimension) 或 (dimension,)
            top_k: 返回结果数量
            
        Returns:
            (文档, 距离分数) 的列表，按相似度排序
        """
        if self.index is None or len(self.documents) == 0:
            return []
        
        # 确保查询向量是2D的
        if len(query_embedding.shape) == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        # 确保是float32类型
        query_embedding = query_embedding.astype('float32')
        
        # 搜索
        top_k = min(top_k, len(self.documents))
        distances, indices = self.index.search(query_embedding, top_k)
        
        # 构建结果
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.documents):
                # 将L2距离转换为相似度分数（距离越小，相似度越高）
                similarity = 1.0 / (1.0 + float(dist))
                results.append((self.documents[idx], similarity))
        
        return results
    
    def save(self, index_path: str, documents_path: str):
        """
        保存索引和文档
        
        Args:
            index_path: 索引文件路径
            documents_path: 文档文件路径
        """
        if self.index is None:
            raise ValueError("没有索引可以保存")
        
        # 保存FAISS索引
        os.makedirs(os.path.dirname(index_path) or '.', exist_ok=True)
        self.faiss.write_index(self.index, index_path)
        
        # 保存文档
        os.makedirs(os.path.dirname(documents_path) or '.', exist_ok=True)
        with open(documents_path, 'wb') as f:
            pickle.dump(self.documents, f)
        
        print(f"索引已保存到: {index_path}")
        print(f"文档已保存到: {documents_path}")
    
    def load(self, index_path: str, documents_path: str):
        """
        加载索引和文档
        
        Args:
            index_path: 索引文件路径
            documents_path: 文档文件路径
        """
        try:
            import faiss
            self.faiss = faiss
        except ImportError:
            raise ImportError("需要安装 faiss: pip install faiss-cpu 或 faiss-gpu")
        
        # 加载FAISS索引
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"索引文件不存在: {index_path}")
        
        self.index = self.faiss.read_index(index_path)
        self.dimension = self.index.d
        
        # 加载文档
        if not os.path.exists(documents_path):
            raise FileNotFoundError(f"文档文件不存在: {documents_path}")
        
        with open(documents_path, 'rb') as f:
            self.documents = pickle.load(f)
        
        print(f"加载索引: {len(self.documents)} 个文档，维度: {self.dimension}")
    
    def get_stats(self) -> dict:
        """
        获取存储统计信息
        
        Returns:
            统计信息字典
        """
        return {
            "total_documents": len(self.documents),
            "dimension": self.dimension,
            "index_size": self.index.ntotal if self.index else 0
        }


# =========================
# 批量构建向量索引工具函数
# =========================

def build_vector_index_from_chunks(
    chunker_type: str = "fixed",
    chunk_dir: str = "knowledge/chunkers/chunker_output",
    output_dir: str = "knowledge/vector_store/index",
    embedder_type: str = "api"
):
    """
    从指定分块策略的切块文件构建向量索引
    
    Args:
        chunker_type: 分块类型 ("fixed" 或 "semantic")
        chunk_dir: 切块文件根目录
        output_dir: 向量索引输出目录
        embedder_type: 嵌入器类型 ("api", "local", "simple")
            - "api": 使用 ModelScope API (需要网络，速度快)
            - "local": 使用本地 Transformers 模型 (无需网络，需要显存)
            - "simple": 使用 TF-IDF (无需网络，速度最快，效果较差)
    """
    import glob
    from pathlib import Path
    
    print(f"\n{'='*60}")
    print(f">> 开始构建 [{chunker_type}] 分块策略的向量索引")
    print(f"{'='*60}\n")
    
    # 1. 确定切块文件目录
    chunk_path = Path(chunk_dir) / chunker_type
    if not chunk_path.exists():
        print(f"[错误] 切块目录不存在: {chunk_path}")
        return
    
    # 2. 读取所有切块文件
    chunk_files = list(chunk_path.glob("*.txt"))
    if not chunk_files:
        print(f"[错误] 在 {chunk_path} 中没有找到切块文件")
        return
    
    print(f"[信息] 找到 {len(chunk_files)} 个切块文件")
    
    # 3. 读取所有切块内容和元数据
    chunks = []
    metadata = []  # 保存元数据（文件名、父块信息等）
    
    # 如果是 parent_child 类型，先读取所有元数据文件
    parent_child_meta = {}
    if chunker_type == "parent_child":
        import json
        meta_files = list(chunk_path.glob("*_metadata.json"))
        print(f"[信息] 找到 {len(meta_files)} 个元数据文件")
        
        for meta_file in meta_files:
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                    # 提取源文件名（去掉 _metadata.json）
                    source_name = meta_file.name.replace('_metadata.json', '')
                    parent_child_meta[source_name] = meta
            except Exception as e:
                print(f"[警告] 读取元数据失败 {meta_file.name}: {e}")
    
    # 读取所有 chunk 文件
    for chunk_file in chunk_files:
        try:
            with open(chunk_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    continue
                
                chunks.append(content)
                
                # 构建元数据
                chunk_meta = {
                    'filename': chunk_file.name,
                    'source': str(chunk_file),
                    'chunker_type': chunker_type
                }
                
                # 如果是 parent_child，添加父块信息
                if chunker_type == "parent_child":
                    # 从文件名提取信息: xxx_chunk_N.txt
                    # 找到对应的源文件和 chunk 索引
                    filename_parts = chunk_file.stem.rsplit('_chunk_', 1)
                    if len(filename_parts) == 2:
                        source_name = filename_parts[0]
                        child_idx = int(filename_parts[1]) - 1  # 文件名是从1开始的
                        
                        # 查找对应的元数据
                        if source_name in parent_child_meta:
                            meta = parent_child_meta[source_name]
                            child_to_parent = meta.get('child_to_parent_map', {})
                            parent_chunks = meta.get('parent_chunks', [])
                            parent_filenames = meta.get('parent_filenames', {})
                            
                            # 获取对应的父块索引和内容
                            parent_idx = child_to_parent.get(str(child_idx))
                            if parent_idx is not None and 0 <= parent_idx < len(parent_chunks):
                                chunk_meta['parent_index'] = parent_idx
                                chunk_meta['parent_chunk'] = parent_chunks[parent_idx]
                                chunk_meta['child_index'] = child_idx
                                # 添加父块文件名（用于实验中的准确率判断）
                                chunk_meta['parent_filename'] = parent_filenames.get(str(parent_idx), parent_filenames.get(parent_idx, ''))
                
                metadata.append(chunk_meta)
                
        except Exception as e:
            print(f"[警告] 读取文件失败 {chunk_file.name}: {e}")
    
    print(f"[信息] 成功读取 {len(chunks)} 个有效切块")
    
    # 如果是 parent_child，显示父子关系统计
    if chunker_type == "parent_child":
        with_parent = sum(1 for m in metadata if 'parent_chunk' in m)
        print(f"[信息] 其中 {with_parent} 个子块包含父块信息")
    
    if not chunks:
        print("[错误] 没有有效的切块内容")
        return
    
    # 4. 初始化嵌入器
    print(f"[配置] 初始化嵌入器: {embedder_type}")
    from knowledge.embeddings import create_embedder
    from config.config import Config
    
    if embedder_type == "api":
        embedder = create_embedder(
            method="api",
            **Config.get_embedding_config()
        )
    elif embedder_type == "local":
        embedder = create_embedder(
            method="local",
            **Config.get_local_embedding_config()
        )
    else:
        embedder = create_embedder(method=embedder_type)
    
    # 对于 simple 类型，需要先训练
    if embedder_type == "simple":
        print(f"[训练] 正在训练 TF-IDF 向量化器...")
        embedder.fit(chunks)
        print(f"[完成] 训练完成")
    
    # 5. 生成向量（批量处理，避免内存溢出）
    print(f"[处理] 开始生成向量...")
    batch_size = 100  # 每批处理100个
    all_embeddings = []
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        try:
            batch_embeddings = embedder.embed(batch)
            all_embeddings.append(batch_embeddings)
            print(f"  [进度] 处理进度: {min(i+batch_size, len(chunks))}/{len(chunks)}")
        except Exception as e:
            print(f"  [警告] 批次 {i}-{i+batch_size} 嵌入失败: {e}")
    
    if not all_embeddings:
        print("[错误] 向量生成失败")
        return
    
    embeddings = np.vstack(all_embeddings)
    print(f"[完成] 向量生成完成，shape: {embeddings.shape}")
    
    # 6. 创建向量存储并添加文档
    print(f"[保存] 创建 FAISS 索引...")
    vector_store = FaissVectorStore(dimension=embeddings.shape[1])
    vector_store.add_documents(embeddings, chunks)
    
    # 7. 保存索引和文档（按分块策略+向量类型创建子目录）
    # 目录命名: {chunker_type}_{embedder_type}
    index_name = f"{chunker_type}_{embedder_type}"
    chunker_output_dir = os.path.join(output_dir, index_name)
    os.makedirs(chunker_output_dir, exist_ok=True)
    
    index_path = os.path.join(chunker_output_dir, "faiss_index.bin")
    documents_path = os.path.join(chunker_output_dir, "documents.pkl")
    metadata_path = os.path.join(chunker_output_dir, "metadata.pkl")
    
    vector_store.save(index_path, documents_path)
    
    # 保存元数据
    with open(metadata_path, 'wb') as f:
        pickle.dump(metadata, f)
    print(f"[完成] 元数据已保存到: {metadata_path}")
    
    # 保存 embedder（如果是 simple 类型，保存 TF-IDF vectorizer 和矩阵）
    if embedder_type == "simple":
        embedder_path = os.path.join(chunker_output_dir, "embedder.pkl")
        # 创建一个包含 vectorizer 和 tfidf_matrix 的对象
        tfidf_data = {
            'vectorizer': embedder.vectorizer,
            'tfidf_matrix': embedder.vectorizer.transform(chunks)  # 重新生成 tfidf_matrix
        }
        with open(embedder_path, 'wb') as f:
            pickle.dump(tfidf_data, f)
        print(f"[完成] TF-IDF embedder 已保存到: {embedder_path}")
    
    # 8. 显示统计信息
    stats = vector_store.get_stats()
    print(f"\n{'='*60}")
    print(f">> 向量索引构建完成！")
    print(f"{'='*60}")
    print(f"[统计信息]:")
    print(f"  - 索引名称: {index_name}")
    print(f"  - 分块策略: {chunker_type}")
    print(f"  - 向量类型: {embedder_type}")
    print(f"  - 文档数量: {stats['total_documents']}")
    print(f"  - 向量维度: {stats['dimension']}")
    print(f"  - 索引路径: {index_path}")
    print(f"  - 文档路径: {documents_path}")
    print(f"{'='*60}\n")


def build_all_vector_indexes(
    chunk_dir: str = "knowledge/chunkers/chunker_output",
    output_dir: str = "knowledge/vector_store/index",
    embedder_type: str = "api"
):
    """
    为所有分块策略构建向量索引
    
    Args:
        chunk_dir: 切块文件根目录
        output_dir: 向量索引输出目录
        embedder_type: 嵌入器类型
    """
    from pathlib import Path
    
    chunk_path = Path(chunk_dir)
    if not chunk_path.exists():
        print(f"[错误] 切块根目录不存在: {chunk_path}")
        return
    
    # 获取所有分块策略子目录
    chunker_types = [d.name for d in chunk_path.iterdir() if d.is_dir()]
    
    if not chunker_types:
        print(f"[错误] 在 {chunk_path} 中没有找到分块策略目录")
        return
    
    print(f"\n[扫描] 发现 {len(chunker_types)} 种分块策略: {', '.join(chunker_types)}\n")
    
    # 为每种分块策略构建索引
    for chunker_type in chunker_types:
        try:
            build_vector_index_from_chunks(
                chunker_type=chunker_type,
                chunk_dir=chunk_dir,
                output_dir=output_dir,
                embedder_type=embedder_type
            )
        except Exception as e:
            print(f"[错误] 构建 [{chunker_type}] 索引失败: {e}\n")


# 如果需要直接运行本文件构建向量索引，可取消以下注释或修改参数:
if __name__ == "__main__":
    # 添加项目根目录到路径，以便导入模块
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    # 方式1: 构建指定分块策略的索引
    build_vector_index_from_chunks(
        chunker_type="parent_child",      # 可选: "fixed" 或 "semantic"
        embedder_type="simple"         # 可选: "api" (网络API), "local" (本地模型), "simple" (TF-IDF)
    )
    
    # 方式2: 构建所有分块策略的索引（注释掉上面的，启用下面的）
    # build_all_vector_indexes(embedder_type="local")
    
    # 示例：使用本地模型，指定GPU设备
    # from knowledge.embeddings import create_embedder
    # embedder = create_embedder(method="local", device="cuda", batch_size=64)
    # 然后传入到构建函数中使用