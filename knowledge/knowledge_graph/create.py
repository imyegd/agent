import json
from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "12345678"

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

# 读取 JSON
with open("knowledge\data\graph\离子注入机知识图谱.json", "r", encoding="utf-8") as f:
    kg_data = json.load(f)


def create_nodes(tx, nodes):
    """创建所有节点，包括详细信息"""
    for node in nodes:
        node_type = node['type']
        node_name = node['name']
        
        # 构建节点属性
        properties = {'name': node_name}
        
        # 如果有 detail_info，将其内容展开为节点属性
        if 'detail_info' in node and node['detail_info']:
            for key, value in node['detail_info'].items():
                # 将 detail_info 中的键值对作为节点属性
                # 键名添加前缀避免与保留字冲突
                prop_key = key.replace(' ', '_').replace('/', '_')
                properties[prop_key] = value
        
        # 构建 SET 子句
        set_clauses = ', '.join([f'n.{k} = ${k}' for k in properties.keys()])
        
        # 根据类型创建不同标签的节点，并设置所有属性
        query = f"MERGE (n:{node_type} {{name: $name}}) SET {set_clauses}"
        tx.run(query, **properties)


def create_edges(tx, edges):
    """创建所有关系"""
    for edge in edges:
        source = edge['source']
        relation = edge['relation'].replace(' ', '_')  # 替换空格
        target = edge['target']
        
        # 使用具体的关系类型
        query = f"""
        MATCH (s {{name: $source}})
        MATCH (t {{name: $target}})
        MERGE (s)-[:`{relation}`]->(t)
        """
        tx.run(query, source=source, target=target)


DATABASE = "generation"  # 指定数据库：papers 或 generation

print(f"开始创建知识图谱...")
print(f"  目标数据库: {DATABASE}")
print(f"  节点数: {len(kg_data['nodes'])}")
print(f"  关系数: {len(kg_data['edges'])}")

with driver.session(database=DATABASE) as session:
    # 清空数据库
    print("\n[0/2] 清空原有数据...")
    session.run("MATCH (n) DETACH DELETE n")
    print("  完成")
    
    # 创建节点
    print("\n[1/2] 创建节点...")
    session.execute_write(create_nodes, kg_data['nodes'])
    print("  完成")
    
    # 创建关系
    print("\n[2/2] 创建关系...")
    session.execute_write(create_edges, kg_data['edges'])
    print("  完成")

driver.close()

print("\n知识图谱创建完成！")
print("在 Neo4j Browser (http://localhost:7474) 查看")
