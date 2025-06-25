import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from base_dune_data import dune_data


# Load .env file variables
load_dotenv()

uri = os.getenv("NEO4J_URI")
user = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(uri, auth=(user, password))


def create_nodes_and_relationships(tx, data):
    for entry in data:
        tx.run(
            """
            MERGE (a:{from_type} {{name: $from_name}})
            MERGE (b:{to_type} {{name: $to_name}})
            MERGE (a)-[r:{rel}]->(b)
            """.format(from_type=entry["type"], to_type=entry["to_type"], rel=entry["rel"]),
            from_name=entry["from"],
            to_name=entry["to"]
        )

with driver.session() as session:
    session.write_transaction(create_nodes_and_relationships, dune_data)
