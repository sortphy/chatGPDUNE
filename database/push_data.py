import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from base_dune_data import dune_data
from langchain_community.embeddings import OllamaEmbeddings  # Changed to match retriever

load_dotenv()
uri = os.getenv("NEO4J_URI")
user = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(uri, auth=(user, password))
embedding_model = OllamaEmbeddings(model="nomic-embed-text")  # Now matches retriever

def check_neo4j_version(tx):
    """Check Neo4j version to determine vector support"""
    result = tx.run("CALL dbms.components() YIELD name, versions, edition RETURN name, versions[0] as version, edition")
    record = result.single()
    return record["version"], record["edition"]

def create_vector_index(tx):
    try:
        # First, let's check what version we're working with
        version, edition = check_neo4j_version(tx)
        print(f"Neo4j Version: {version}, Edition: {edition}")
        
        # Create the index that the retriever expects: "dune_chunks"
        # Try vector index first for newer versions
        if version.startswith(("5.", "2025.")) and "enterprise" in edition.lower():
            try:
                tx.run("""
                CREATE VECTOR INDEX dune_chunks IF NOT EXISTS
                FOR (n:DuneChunk) ON (n.embedding)
                OPTIONS {
                    indexConfig: {
                        `vector.dimensions`: 768,
                        `vector.similarity_function`: 'cosine'
                    }
                }
                """)
                print("Vector index 'dune_chunks' created successfully.")
                return "vector"
            except Exception as ve:
                print(f"Vector index failed: {ve}")
                # Fall back to text index
        
        # Create text index with the exact name the retriever expects
        tx.run("""
        CREATE INDEX dune_chunks IF NOT EXISTS
        FOR (n:DuneChunk) ON (n.text)
        """)
        print("Text index 'dune_chunks' created successfully.")
        return "text"
            
    except Exception as e:
        print(f"Error creating index: {e}")
        return "none"

def push_strings(tx, texts):
    for i, text in enumerate(texts):
        try:
            vector = embedding_model.embed_query(text)
            print(f"Processing text {i+1}/{len(texts)}: {text[:50]}...")
            
            # Use label "DuneChunk" to match your other pusher
            tx.run(
                """
                MERGE (n:DuneChunk {text: $text})
                SET n.embedding = $embedding, n.id = $id
                """,
                text=text,
                embedding=vector,
                id=i
            )
        except Exception as e:
            print(f"Error processing text '{text}': {e}")

def verify_data(tx):
    """Verify that data was inserted correctly"""
    result = tx.run("MATCH (n:DuneChunk) RETURN count(n) as count")
    count = result.single()["count"]
    print(f"Total nodes inserted: {count}")
    
    # Show a sample
    result = tx.run("MATCH (n:DuneChunk) RETURN n.text as text LIMIT 3")
    print("Sample data:")
    for record in result:
        print(f"  - {record['text']}")

def cleanup_old_data(tx):
    """Remove old chunk nodes if they exist"""
    # Clean up old Chunk nodes
    result = tx.run("MATCH (n:Chunk) RETURN count(n) as count")
    old_count = result.single()["count"]
    if old_count > 0:
        print(f"Found {old_count} old Chunk nodes, removing them...")
        tx.run("MATCH (n:Chunk) DETACH DELETE n")
        print("Old Chunk nodes removed.")
    
    # Clean up old dune_chunks nodes  
    result = tx.run("MATCH (n:dune_chunks) RETURN count(n) as count")
    old_count2 = result.single()["count"]
    if old_count2 > 0:
        print(f"Found {old_count2} old dune_chunks nodes, removing them...")
        tx.run("MATCH (n:dune_chunks) DETACH DELETE n")
        print("Old dune_chunks nodes removed.")

# Main execution
try:
    with driver.session() as session:
        print("Cleaning up old data...")
        session.execute_write(cleanup_old_data)
        
        print("Creating index...")
        index_type = session.execute_write(create_vector_index)
        
        print("Inserting data...")
        session.execute_write(push_strings, dune_data)
        
        print("Verifying data...")
        session.execute_read(verify_data)
        
    print("✅ Process completed successfully!")
    print(f"✅ Data is now compatible with your existing retriever!")
    
except Exception as e:
    print(f"❌ Error during execution: {e}")
    
finally:
    driver.close()