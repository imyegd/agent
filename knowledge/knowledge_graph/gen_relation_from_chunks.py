"""
从 parent_child chunks 生成知识图谱三元组
保留节点与 chunk 的对应关系，用于 RAG 检索增强
"""
import os
import json
from typing import List, Dict
from openai import OpenAI
from neo4j import GraphDatabase
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.config import Config


class KGGenerator:
    """知识图谱生成器"""
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str, database: str = "papers"):
        self.client = OpenAI(
            base_url=Config.BASE_URL,
            api_key=Config.API_KEY
        )
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        self.database = database
        
        # 模型列表，用于切换
        self.available_models = [
            'Qwen/Qwen3-VL-30B-A3B-Instruct', 
            'Qwen/Qwen2.5-7B-Instruct',
            'Qwen/Qwen3-8B',
            'Qwen/Qwen3-4B',
            'Qwen/Qwen3-VL-4B-Instruct'
        ]
        self.current_model_index = 0
        
    def extract_triples(self, chunk_text: str, chunk_file: str) -> List[Dict]:
        """
        从 chunk 中提取三元组
        
        Args:
            chunk_text: chunk 文本
            chunk_file: chunk 文件名
            
        Returns:
            三元组列表 [{'subject': ..., 'predicate': ..., 'object': ...}, ...]
        """
        prompt = f"""从下面的文本中提取知识图谱三元组。

要求：
1. 提取格式：(主体, 关系, 客体)
2. 主体和客体应该是具体的实体（如：加速器、束流、磁场等）
3. 关系应该是动词或关系词（如：用于、产生、控制、影响等）
4. 只提取重要的专业知识关系，数量控制在3-10个
5. 返回 JSON 格式：[{{"subject": "主体", "predicate": "关系", "object": "客体"}}, ...]

文本内容：
{chunk_text[:1500]}

请直接返回 JSON 数组，不要有其他内容。"""

        # 尝试所有可用模型
        for attempt in range(len(self.available_models)):
            current_model = self.available_models[self.current_model_index]
            
            try:
                response = self.client.chat.completions.create(
                    model=current_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )
                
                result = response.choices[0].message.content.strip()
                
                # 提取 JSON
                if "```json" in result:
                    result = result.split("```json")[1].split("```")[0].strip()
                elif "```" in result:
                    result = result.split("```")[1].split("```")[0].strip()
                
                triples = json.loads(result)
                
                # 为每个三元组添加 chunk 信息
                for triple in triples:
                    triple['chunk_file'] = chunk_file
                
                return triples
                
            except Exception as e:
                error_msg = str(e)
                
                # 检查是否是限流错误
                if "429" in error_msg or "rate limit" in error_msg.lower() or "quota" in error_msg.lower():
                    print(f"  [警告] 模型 {current_model} 达到限制，切换到下一个模型")
                    # 切换到下一个模型
                    self.current_model_index = (self.current_model_index + 1) % len(self.available_models)
                    continue
                else:
                    print(f"  [错误] 提取三元组失败: {e}")
                    return []
        
        print(f"  [错误] 所有模型都已达到限制")
        return []
    
    def store_triples(self, triples: List[Dict]):
        """
        将三元组存入 Neo4j
        为每个实体节点添加关联的 chunk_files 列表
        
        Args:
            triples: 三元组列表
        """
        with self.driver.session(database=self.database) as session:
            for triple in triples:
                subject = triple['subject']
                predicate = triple['predicate']
                obj = triple['object']
                chunk_file = triple['chunk_file']
                
                # 创建或更新节点，添加 chunk_file 到列表中
                query = """
                MERGE (s:Entity {name: $subject})
                ON CREATE SET s.chunk_files = [$chunk_file]
                ON MATCH SET s.chunk_files = 
                    CASE 
                        WHEN NOT $chunk_file IN s.chunk_files 
                        THEN s.chunk_files + $chunk_file
                        ELSE s.chunk_files
                    END
                
                MERGE (o:Entity {name: $object})
                ON CREATE SET o.chunk_files = [$chunk_file]
                ON MATCH SET o.chunk_files = 
                    CASE 
                        WHEN NOT $chunk_file IN o.chunk_files 
                        THEN o.chunk_files + $chunk_file
                        ELSE o.chunk_files
                    END
                
                MERGE (s)-[r:RELATION {type: $predicate, chunk_file: $chunk_file}]->(o)
                """
                
                session.run(query, subject=subject, predicate=predicate, 
                           object=obj, chunk_file=chunk_file)
    
    def process_chunks(self, chunk_dir: str, max_chunks: int = None, start_from: int = 0, clear_db: bool = True):
        """
        处理所有 chunks，生成知识图谱
        
        Args:
            chunk_dir: chunk 目录
            max_chunks: 最大处理数量（用于测试）
            start_from: 从第几个 chunk 开始处理（0-based，用于续传）
            clear_db: 是否清空数据库
        """
        print("=" * 100)
        print("从 Chunks 生成知识图谱")
        print("=" * 100)
        
        # 清空数据库
        if clear_db:
            print(f"\n[0/3] 清空数据库 {self.database}...")
            with self.driver.session(database=self.database) as session:
                session.run("MATCH (n) DETACH DELETE n")
            print("  完成")
        else:
            print(f"\n[0/3] 跳过清空数据库（续传模式）")
        
        # 获取所有 chunk 文件
        chunk_files = sorted([f for f in os.listdir(chunk_dir) 
                             if f.endswith('.txt') and not f.endswith('_metadata.json')])
        
        if max_chunks:
            chunk_files = chunk_files[:max_chunks]
        
        print(f"\n[1/3] 找到 {len(chunk_files)} 个 chunk 文件")
        if start_from > 0:
            print(f"  从第 {start_from + 1} 个开始处理（跳过前 {start_from} 个）")
            chunk_files = chunk_files[start_from:]
        print(f"[2/3] 提取三元组...")
        print()
        
        total_triples = 0
        
        for i, chunk_file in enumerate(chunk_files, start_from + 1):
            chunk_path = os.path.join(chunk_dir, chunk_file)
            
            try:
                with open(chunk_path, 'r', encoding='utf-8') as f:
                    chunk_text = f.read()
                
                if not chunk_text.strip():
                    continue
                
                print(f"[{i}/{len(chunk_files)}] 处理: {chunk_file}")
                
                # 提取三元组
                triples = self.extract_triples(chunk_text, chunk_file)
                
                if triples:
                    print(f"  提取到 {len(triples)} 个三元组")
                    # 存储到 Neo4j
                    self.store_triples(triples)
                    total_triples += len(triples)
                else:
                    print(f"  未提取到三元组")
                
            except Exception as e:
                print(f"  [错误] 处理失败: {e}")
        
        print(f"\n[3/3] 完成！")
        print(f"\n" + "=" * 100)
        print(f"知识图谱生成完成")
        print(f"  数据库: {self.database}")
        print(f"  本次处理 chunks: {len(chunk_files)}")
        print(f"  本次生成三元组: {total_triples}")
        print("=" * 100)
    
    def close(self):
        """关闭连接"""
        self.driver.close()


class KGRetriever:
    """知识图谱检索器（用于 RAG）"""
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str, database: str = "papers"):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        self.database = database
    
    def retrieve_related_chunks(self, query_entities: List[str], max_neighbors: int = 5) -> List[str]:
        """
        根据查询实体，检索相关节点及其邻居对应的 chunks
        
        Args:
            query_entities: 查询实体列表（从查询中提取的关键实体）
            max_neighbors: 每个实体的最大邻居数
            
        Returns:
            相关的 chunk 文件列表
        """
        with self.driver.session(database=self.database) as session:
            chunk_files = set()
            
            for entity in query_entities:
                # 查找实体节点及其邻居
                query = """
                MATCH (e:Entity {name: $entity})
                OPTIONAL MATCH (e)-[r]-(neighbor:Entity)
                WITH e, collect(DISTINCT neighbor)[0..$max_neighbors] as neighbors
                RETURN e.chunk_files as entity_chunks, 
                       [n IN neighbors | n.chunk_files] as neighbor_chunks
                """
                
                result = session.run(query, entity=entity, max_neighbors=max_neighbors)
                
                for record in result:
                    # 添加实体自己的 chunks
                    if record['entity_chunks']:
                        chunk_files.update(record['entity_chunks'])
                    
                    # 添加邻居的 chunks
                    if record['neighbor_chunks']:
                        for neighbor_chunk_list in record['neighbor_chunks']:
                            if neighbor_chunk_list:
                                chunk_files.update(neighbor_chunk_list)
            
            return list(chunk_files)
    
    def close(self):
        """关闭连接"""
        self.driver.close()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='从 chunks 生成知识图谱')
    parser.add_argument('--chunk-dir', type=str, 
                       default='knowledge/chunkers/chunker_output/chapter',
                       help='chunk 目录')
    parser.add_argument('--neo4j-uri', type=str, 
                       default='bolt://localhost:7687',
                       help='Neo4j URI')
    parser.add_argument('--neo4j-user', type=str, 
                       default='neo4j',
                       help='Neo4j 用户名')
    parser.add_argument('--neo4j-password', type=str, 
                       default='12345678',
                       help='Neo4j 密码')
    parser.add_argument('--max-chunks', type=int, 
                       default=None,
                       help='最大处理 chunk 数量（测试用）')
    parser.add_argument('--database', type=str,
                       default='papers',
                       help='Neo4j 数据库名称（papers 或 generation）')
    parser.add_argument('--start-from', type=int,
                       default=600,
                       help='从第几个 chunk 开始处理（0-based，用于续传）')
    parser.add_argument('--no-clear', action='store_true',
                       help='不清空数据库（续传模式）')
    
    args = parser.parse_args()
    
    # 生成知识图谱
    generator = KGGenerator(
        neo4j_uri=args.neo4j_uri,
        neo4j_user=args.neo4j_user,
        neo4j_password=args.neo4j_password,
        database=args.database
    )
    
    try:
        generator.process_chunks(
            chunk_dir=args.chunk_dir, 
            max_chunks=args.max_chunks,
            start_from=args.start_from,
            clear_db=not args.no_clear
        )
    finally:
        generator.close()


if __name__ == "__main__":
    main()
