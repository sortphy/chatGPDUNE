from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("NEO4J_URI")
user = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(uri, auth=(user, password))

def get_all_characters(tx):
    result = tx.run("MATCH (c:Character) RETURN c.name AS name")
    return [record["name"] for record in result]

with driver.session() as session:
    characters = session.read_transaction(get_all_characters)
    print("Characters:", characters)


## this is just to test the datbase it will retriweve all characters from the database