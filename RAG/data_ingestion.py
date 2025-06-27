import os, subprocess, time, shutil, requests, atexit
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Neo4jVector
from langchain_community.document_loaders import TextLoader, PyPDFLoader, UnstructuredHTMLLoader, UnstructuredMarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from neo4j import GraphDatabase
from tqdm import tqdm
from dotenv import load_dotenv


# Load .env file variables
load_dotenv()


# Configuration
NEO4J_URI      = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
OLLAMA_URL     = os.getenv("OLLAMA_HOST", "http://localhost:11434")
EMBED_MODEL    = "nomic-embed-text"

# Tweakable settings
CHUNK_SIZE = 512          # Size of each text chunk
CHUNK_OVERLAP = 20        # Overlap between chunks
BATCH_SIZE = 200          # How many chunks to process at once
PROCESSING_TIMEOUT = 30   # Ollama startup timeout
DATA_DIR = "./data"       # Where your files are
INDEX_NAME = "dune_chunks" # Neo4j index name
NODE_LABEL = "DuneChunk"  # Neo4j node label

# Supported file extensions
SUPPORTED_EXTENSIONS = ['.txt', '.pdf', '.html', '.htm', '.md', '.markdown']

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
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
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

def get_appropriate_loader(file_path):
    """Return the appropriate LangChain loader for the file type"""
    _, ext = os.path.splitext(file_path.lower())
    
    if ext == '.pdf':
        return PyPDFLoader(file_path)
    elif ext in ['.html', '.htm']:
        return UnstructuredHTMLLoader(file_path)
    elif ext in ['.md', '.markdown']:
        return UnstructuredMarkdownLoader(file_path)
    elif ext == '.txt':
        # Try different encodings for text files
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                return TextLoader(file_path, encoding=encoding)
            except UnicodeDecodeError:
                continue
        # If all encodings fail, try with autodetect
        return TextLoader(file_path, autodetect_encoding=True)
    else:
        raise ValueError(f"Unsupported file extension: {ext}")

def load_and_chunk_documents(data_dir=DATA_DIR):
    """Load and chunk documents from various file formats"""
    docs = []
    
    # Get all supported files
    all_files = os.listdir(data_dir)
    supported_files = []
    for fn in all_files:
        _, ext = os.path.splitext(fn.lower())
        if ext in SUPPORTED_EXTENSIONS:
            supported_files.append(fn)
    
    if not supported_files:
        print(f"⚠ No supported files found in {data_dir}")
        print(f"Supported extensions: {', '.join(SUPPORTED_EXTENSIONS)}")
        return []
    
    print(f"Loading and chunking documents from {data_dir}...")
    print(f"Found {len(supported_files)} supported files: {', '.join(SUPPORTED_EXTENSIONS)}")
    
    for fn in tqdm(supported_files, desc="Loading files"):
        file_path = os.path.join(data_dir, fn)
        _, ext = os.path.splitext(fn.lower())
        
        try:
            loader = get_appropriate_loader(file_path)
            file_docs = loader.load()
            
            # Add metadata about the source file and type
            for doc in file_docs:
                doc.metadata['source_file'] = fn
                doc.metadata['file_type'] = ext
                doc.metadata['file_path'] = file_path
            
            docs.extend(file_docs)
            tqdm.write(f"✓ Loaded {fn} ({ext.upper()}) - {len(file_docs)} document(s)")
            
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
    
    # Start timing the embedding/storage process
    start_time = time.time()
    
    # Set environment variables to ensure Neo4j credentials are available
    # This is the primary fix for the username issue
    os.environ['NEO4J_USER'] = NEO4J_USER
    os.environ['NEO4J_PASSWORD'] = NEO4J_PASSWORD
    os.environ['NEO4J_URI'] = NEO4J_URI
    
    # Process in batches with progress bar
    total_batches = (len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE
    successful_batches = 0
    
    for i in tqdm(range(0, len(chunks), BATCH_SIZE), 
                  desc="Processing batches", 
                  total=total_batches):
        batch = chunks[i:i+BATCH_SIZE]
        try:
            # Method 1: Try with explicit parameters (most compatible)
            try:
                Neo4jVector.from_documents(
                    batch, embeddings,
                    url=NEO4J_URI, 
                    username=NEO4J_USER, 
                    password=NEO4J_PASSWORD,
                    index_name=INDEX_NAME, 
                    node_label=NODE_LABEL,
                    embedding_node_property="embedding", 
                    text_node_property="text"
                )
                successful_batches += 1
            except TypeError:
                # Method 2: Try without explicit username/password if the above fails
                # Some versions expect these to be in environment variables only
                Neo4jVector.from_documents(
                    batch, embeddings,
                    url=NEO4J_URI,
                    index_name=INDEX_NAME, 
                    node_label=NODE_LABEL,
                    embedding_node_property="embedding", 
                    text_node_property="text"
                )
                successful_batches += 1
                
        except Exception as e:
            tqdm.write(f"✗ Error processing batch {i//BATCH_SIZE + 1}: {e}")
            # Try alternative approach for this batch
            try:
                # Method 3: Initialize Neo4jVector separately then add documents
                vector_store = Neo4jVector(
                    embeddings,
                    url=NEO4J_URI,
                    username=NEO4J_USER,
                    password=NEO4J_PASSWORD,
                    index_name=INDEX_NAME,
                    node_label=NODE_LABEL,
                    embedding_node_property="embedding",
                    text_node_property="text"
                )
                vector_store.add_documents(batch)
                successful_batches += 1
                tqdm.write(f"✓ Batch {i//BATCH_SIZE + 1} processed with alternative method")
            except Exception as e2:
                tqdm.write(f"✗ Alternative method also failed for batch {i//BATCH_SIZE + 1}: {e2}")
                continue
    
    # Calculate and display timing
    elapsed_time = time.time() - start_time
    hours = elapsed_time / 3600
    minutes = (elapsed_time % 3600) / 60
    
    print(f"✓ Neo4j populated! Successfully processed {successful_batches}/{total_batches} batches")
    print(f"✓ Index: {INDEX_NAME}, Node Label: {NODE_LABEL}")
    print(f"✓ Embedding generation and storage took: {hours:.1f} hours ({minutes:.1f} minutes)")
    print(f"✓ Average time per chunk: {elapsed_time/len(chunks):.2f} seconds")

def verify_environment_variables():
    """Verify all required environment variables are set"""
    required_vars = ['NEO4J_URI', 'NEO4J_USER', 'NEO4J_PASSWORD']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file or set these variables.")
        raise RuntimeError(f"Missing environment variables: {missing_vars}")
    
    print("✓ All required environment variables are set")

def check_dependencies():
    """Check if required packages for different file types are installed"""
    missing_packages = []
    
    # Check for PDF support
    try:
        import pypdf
    except ImportError:
        missing_packages.append("pypdf (for PDF files)")
    
    # Check for HTML/Markdown support
    try:
        import unstructured
    except ImportError:
        missing_packages.append("unstructured (for HTML and Markdown files)")
    
    if missing_packages:
        print(f"⚠ Missing optional packages: {', '.join(missing_packages)}")
        print("Install with: pip install pypdf unstructured")
        print("You can still process TXT files without these packages.")
    else:
        print("✓ All optional packages for file format support are installed")

def main():
    print("=" * 60)
    print("MULTI-FORMAT RAG DATA INGESTION")
    print("=" * 60)
    print(f"Data directory: {DATA_DIR}")
    print(f"Neo4j URI: {NEO4J_URI}")
    print(f"Ollama URL: {OLLAMA_URL}")
    print(f"Embedding model: {EMBED_MODEL}")
    print(f"Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}")
    print("=" * 60)
    
    # Start timing the entire process
    total_start_time = time.time()
    
    # Verify environment variables first
    verify_environment_variables()
    
    # Check dependencies
    check_dependencies()
    
    # Create data directory if it doesn't exist
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Create sample files if data directory is empty
    if not any(os.path.splitext(fn)[1].lower() in SUPPORTED_EXTENSIONS for fn in os.listdir(DATA_DIR)):
        # Create sample TXT file
        with open(os.path.join(DATA_DIR, "dune_excerpt.txt"), "w", encoding='utf-8') as f:
            f.write("The spice must flow… Fear is the mind-killer. He who controls the spice controls the universe.")
        
        # Create sample Markdown file
        with open(os.path.join(DATA_DIR, "sample.md"), "w", encoding='utf-8') as f:
            f.write("# Sample Markdown\n\nThis is a **sample** markdown file for testing.\n\n## Features\n\n- Supports multiple formats\n- Automatic file type detection\n- Metadata preservation")
        
        print(f"✓ Created sample files in {DATA_DIR}")
    
    try:
        # Step 1: Clear existing data
        clear_start = time.time()
        clear_neo4j_database()
        clear_time = time.time() - clear_start
        print(f"✓ Database clearing took: {clear_time:.1f} seconds")
        
        # Step 2: Load and chunk documents
        chunk_start = time.time()
        chunks = load_and_chunk_documents()
        chunk_time = time.time() - chunk_start
        print(f"✓ Document loading and chunking took: {chunk_time:.1f} seconds")
        
        if not chunks:
            print("⚠ No chunks to process. Exiting.")
            return
        
        # Step 3: Generate embeddings and populate Neo4j
        populate_neo4j_with_chunks(chunks)
        
        # Calculate total time
        total_elapsed = time.time() - total_start_time
        total_hours = total_elapsed / 3600
        total_minutes = (total_elapsed % 3600) / 60
        
        print("\n" + "=" * 60)
        print("✅ INGESTION COMPLETE!")
        print(f"✅ Total processing time: {total_hours:.1f} hours ({total_minutes:.1f} minutes)")
        print(f"✅ Processed {len(chunks)} chunks total")
        
        # Show file type breakdown
        file_types = {}
        for chunk in chunks:
            file_type = chunk.metadata.get('file_type', 'unknown')
            file_types[file_type] = file_types.get(file_type, 0) + 1
        
        print("✅ File type breakdown:")
        for file_type, count in file_types.items():
            print(f"   {file_type.upper()}: {count} chunks")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error during ingestion: {e}")
        raise

if __name__ == "__main__":
    main()