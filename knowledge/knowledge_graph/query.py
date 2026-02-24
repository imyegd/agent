
from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "12345678"   # 换成你自己的
DATABASE = "papers"  # 选择数据库：papers 或 generation

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

def query_structure(tx, variable_name):
    result = tx.run("""
    MATCH (v:Variable {name: $name})
    OPTIONAL MATCH (v)-[:BELONGS_TO]->(s)
    OPTIONAL MATCH (v)-[:HAS_FUNCTION]->(f)
    RETURN s.name AS subsystem, f.name AS function
    """, name=variable_name)
    return result.single()

with driver.session(database=DATABASE) as session:
    record = session.execute_read(query_structure, "加速电源电压")
    print(f"查询数据库: {DATABASE}")
    print(record)


def get_diagnosis_context(tx, variable_name):
    result = tx.run("""
    MATCH (v:Variable {name: $name})
    OPTIONAL MATCH (v)-[:BELONGS_TO]->(s)
    OPTIONAL MATCH (v)-[:HAS_FUNCTION]->(f)
    OPTIONAL MATCH (v)-[:MAY_AFFECT]->(m)
    RETURN v.name AS variable,
           s.name AS subsystem,
           f.name AS function,
           m.name AS metric
    """, name=variable_name)
    return dict(result.single())

with driver.session(database=DATABASE) as session:
    context = session.execute_read(get_diagnosis_context, "灯丝电源电流")
    print(context)

