from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Neo4jVector
from neo4j import GraphDatabase
import os

from dotenv import load_dotenv


# Load .env file variables
load_dotenv()


# Configuration
NEO4J_URI      = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

def get_neo4j_retriever():
    embeddings = OllamaEmbeddings(model="nomic-embed-text")

    vectorstore = Neo4jVector.from_existing_index(
        embeddings,
        url=NEO4J_URI,
        username=NEO4J_USER,
        password=NEO4J_PASSWORD,
        index_name="dune_chunks",
        text_node_property="text",
    )
    return vectorstore.as_retriever()

if __name__ == "__main__":
    retriever = get_neo4j_retriever()
    query = "What is the importance of spice?"
    docs = retriever.invoke(query)
    print(f"Retrieved documents for query \"{query}\":")
    for doc in docs:
        print(f"- {doc.page_content[:100]}...")
