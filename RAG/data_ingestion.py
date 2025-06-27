import os, subprocess, time, shutil, requests, atexit
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Neo4jVector
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from neo4j import GraphDatabase
from tqdm import tqdm

# Configuration
NEO4J_URI      = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
OLLAMA_URL     = os.getenv("OLLAMA_HOST", "http://localhost:11434")
EMBED_MODEL    = "nomic-embed-text"

# Tweakable settings
CHUNK_SIZE = 512          # Size of each text chunk
CHUNK_OVERLAP = 20        # Overlap between chunks
BATCH_SIZE = 50           # How many chunks to process at once
PROCESSING_TIMEOUT = 30   # Ollama startup timeout
DATA_DIR = "./data"       # Where your txt files are
INDEX_NAME = "dune_chunks" # Neo4j index name
NODE_LABEL = "DuneChunk"  # Neo4j node label

def ensure_ollama(model=EMBED_MODEL, timeout=PROCESSING_TIMEOUT):
    if not shutil.which("ollama"):
        raise RuntimeError("`ollama` binary not found in PATH.")

    # 1) Is the server already up?
    try:
        requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        return                  # It's running – nothing to do.
    except requests.exceptions.RequestException:
        pass

    # 2) Start server in background (silent).
    proc = subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    atexit.register(proc.terminate)       # Kill it on script exit.

    # 3) Wait until the API answers.
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            requests.get(f"{OLLAMA_URL}/api/tags", timeout=1)
            break
        except requests.exceptions.RequestException:
            time.sleep(0.5)
    else:
        raise RuntimeError("Ollama server did not start in time.")

    # 4) Make sure the model is downloaded.
    subprocess.run(["ollama", "pull", model], check=True)

def clear_neo4j_database():
    """Clear existing chunks from Neo4j database"""
    print("Clearing existing data from Neo4j...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    try:
        with driver.session() as session:
            result = session.run(f"MATCH (n:{NODE_LABEL}) RETURN count(n) as count")
            count = result.single()["count"]
            if count > 0:
                session.run(f"MATCH (n:{NODE_LABEL}) DETACH DELETE n")
                print(f"✓ Cleared {count} existing chunks from database")
            else:
                print("✓ Database was already empty")
    except Exception as e:
        print(f"⚠ Warning: Could not clear database: {e}")
    finally:
        driver.close()

def load_and_chunk_documents(data_dir=DATA_DIR):
    docs = []
    files = [fn for fn in os.listdir(data_dir) if fn.endswith(".txt")]
    
    if not files:
        print(f"⚠ No .txt files found in {data_dir}")
        return []
    
    print(f"Loading and chunking documents from {data_dir}...")
    for fn in tqdm(files, desc="Loading files"):
        file_path = os.path.join(data_dir, fn)
        try:
            # Try UTF-8 first (most common)
            loader = TextLoader(file_path, encoding='utf-8')
            docs.extend(loader.load())
            tqdm.write(f"✓ Loaded {fn} with UTF-8 encoding")
        except UnicodeDecodeError:
            try:
                # Try UTF-8 with error handling
                loader = TextLoader(file_path, encoding='utf-8', autodetect_encoding=True)
                docs.extend(loader.load())
                tqdm.write(f"✓ Loaded {fn} with UTF-8 encoding (with error handling)")
            except Exception as e:
                try:
                    # Try latin-1 as fallback (can decode any byte sequence)
                    loader = TextLoader(file_path, encoding='latin-1')
                    docs.extend(loader.load())
                    tqdm.write(f"✓ Loaded {fn} with latin-1 encoding")
                except Exception as e2:
                    tqdm.write(f"✗ Failed to load {fn}: {e2}")
                    continue
        except Exception as e:
            tqdm.write(f"✗ Failed to load {fn}: {e}")
            continue
    
    if not docs:
        raise RuntimeError("No documents were successfully loaded!")
    
    print(f"Splitting {len(docs)} documents into chunks...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, 
        chunk_overlap=CHUNK_OVERLAP
    )
    chunks = splitter.split_documents(docs)
    print(f"✓ Created {len(chunks)} chunks (chunk_size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    return chunks

def populate_neo4j_with_chunks(chunks):
    ensure_ollama()
    embeddings = OllamaEmbeddings(model=EMBED_MODEL)
    
    print(f"Generating embeddings and storing {len(chunks)} chunks in Neo4j...")
    print(f"Using model: {EMBED_MODEL}, batch_size: {BATCH_SIZE}")
    
    # Process in batches with progress bar
    total_batches = (len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE
    successful_batches = 0
    
    for i in tqdm(range(0, len(chunks), BATCH_SIZE), 
                  desc="Processing batches", 
                  total=total_batches):
        batch = chunks[i:i+BATCH_SIZE]
        try:
            Neo4jVector.from_documents(
                batch, embeddings,
                url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD,
                index_name=INDEX_NAME, node_label=NODE_LABEL,
                embedding_node_property="embedding", text_node_property="text"
            )
            successful_batches += 1
        except Exception as e:
            tqdm.write(f"✗ Error processing batch {i//BATCH_SIZE + 1}: {e}")
            continue
    
    print(f"✓ Neo4j populated! Successfully processed {successful_batches}/{total_batches} batches")
    print(f"✓ Index: {INDEX_NAME}, Node Label: {NODE_LABEL}")

def main():
    print("=" * 60)
    print("DUNE RAG DATA INGESTION")
    print("=" * 60)
    print(f"Data directory: {DATA_DIR}")
    print(f"Neo4j URI: {NEO4J_URI}")
    print(f"Ollama URL: {OLLAMA_URL}")
    print(f"Embedding model: {EMBED_MODEL}")
    print("=" * 60)
    
    # Create data directory if it doesn't exist
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Create sample file if data directory is empty
    if not any(fn.endswith('.txt') for fn in os.listdir(DATA_DIR)):
        with open(os.path.join(DATA_DIR, "dune_excerpt.txt"), "w", encoding='utf-8') as f:
            f.write("The spice must flow… Fear is the mind-killer. He who controls the spice controls the universe.")
        print(f"✓ Created sample file in {DATA_DIR}")
    
    try:
        # Step 1: Clear existing data
        clear_neo4j_database()
        
        # Step 2: Load and chunk documents
        chunks = load_and_chunk_documents()
        
        if not chunks:
            print("⚠ No chunks to process. Exiting.")
            return
        
        # Step 3: Generate embeddings and populate Neo4j
        populate_neo4j_with_chunks(chunks)
        
        print("\n" + "=" * 60)
        print("✅ INGESTION COMPLETE!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error during ingestion: {e}")
        raise

if __name__ == "__main__":
    main()