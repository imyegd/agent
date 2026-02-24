import json
import re
from neo4j import GraphDatabase

# --- 配置区 ---
URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "12345678"
DATABASE = "papers"

# 权重设置
TOOL_CALL_WEIGHT = 2.0
KG_NODE_WEIGHT = 3.0

def fetch_kg_nodes():
    """从 Neo4j 获取所有实体的名称"""
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    node_names = set()
    
    # 注意：这里假设你的节点属性名是 'name'，如果是 'title' 请修改
    cypher_query = "MATCH (n) RETURN DISTINCT n.name as name"
    
    try:
        with driver.session(database=DATABASE) as session:
            result = session.run(cypher_query)
            for record in result:
                name = record["name"]
                if name and len(str(name)) > 1: # 过滤掉空值或过短的干扰词
                    node_names.add(re.escape(str(name))) # 自动处理正则转义
    except Exception as e:
        print(f"连接数据库出错: {e}")
    finally:
        driver.close()
    
    return sorted(list(node_names), key=len, reverse=True) # 长度倒序排列，防止短词优先匹配

def generate_json():
    nodes = fetch_kg_nodes()
    if not nodes:
        print("未获取到节点，请检查数据库或查询语句！")
        return

    # 构建针对 KG 节点的正则表达式：匹配单词边界内的节点词
    # 使用 \b 确保是完整匹配词汇，而不是词的一部分
    kg_regex = f"\\b({'|'.join(nodes)})\\b"

    # 构造符合 Swift 格式的字典
    custom_config = {
        # 保留原有的工具调用权重
        "<tool_call>.+?</tool_call>": [TOOL_CALL_WEIGHT],
        # 添加针对你 KG 节点的权重
        kg_regex: [KG_NODE_WEIGHT]
    }

    output_path = "custom_agent.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(custom_config, f, ensure_ascii=False, indent=4)
    
    print(f"成功！已提取 {len(nodes)} 个节点，配置文件已保存至: {output_path}")

if __name__ == "__main__":
    generate_json()