import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from base_dune_data import dune_data
from langchain_ollama import OllamaEmbeddings  # trocado para langchain_ollama

# Load env
load_dotenv()
uri = os.getenv("NEO4J_URI")
user = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(uri, auth=(user, password))
embedding_model = OllamaEmbeddings(model="nomic-embed-text")

def push_strings(tx, texts):
    for text in texts:
        vector = embedding_model.embed_query(text)
        tx.run(
            """
            MERGE (n:ManualEntry {text: $text})
            SET n.embedding = $embedding
            """,
            text=text,
            embedding=vector
        )

with driver.session() as session:
    session.execute_write(push_strings, dune_data)  # updated from write_transaction

print("✅ Strings com embedding salvas no Neo4j como :ManualEntry.")
