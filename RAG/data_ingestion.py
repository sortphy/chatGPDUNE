# backend/data_ingestion.py (continued)

from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Neo4jVector
from neo4j import GraphDatabase
import os

# Neo4j connection details (replace with your actual credentials)
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def populate_neo4j_with_chunks(chunks):
    embeddings = OllamaEmbeddings(model="nomic-embed-text")

    # Initialize Neo4jVector store
    # This will create a vector index in Neo4j if it doesn't exist
    vectorstore = Neo4jVector.from_documents(
        chunks,
        embeddings,
        url=NEO4J_URI,
        username=NEO4J_USERNAME,
        password=NEO4J_PASSWORD,
        index_name="dune_chunks",  # Name of your vector index
        node_label="DuneChunk",    # Label for nodes storing chunks
        embedding_node_property="embedding", # Property for embeddings
        text_node_property="text", # Property for chunk text
    )
    print("Neo4j populated with document chunks.")

if __name__ == "__main__":
    # ... (previous code for loading and chunking)
    os.makedirs("./data", exist_ok=True)
    with open("./data/dune_excerpt.txt", "w") as f:
        f.write("The spice must flow. It is essential for space travel and extending life. Arrakis is the source of the spice, also known as Melange. The Fremen are the native inhabitants of Arrakis, adapted to its harsh desert environment.")

    chunks = load_and_chunk_documents()
    populate_neo4j_with_chunks(chunks)
