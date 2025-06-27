import os, subprocess, time, shutil, requests, atexit
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Neo4jVector
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from neo4j import GraphDatabase

NEO4J_URI      = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
OLLAMA_URL     = os.getenv("OLLAMA_HOST", "http://localhost:11434")
EMBED_MODEL    = "nomic-embed-text"

def ensure_ollama(model=EMBED_MODEL, timeout=30):
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

def load_and_chunk_documents(data_dir="./data"):
    docs = []
    for fn in os.listdir(data_dir):
        if fn.endswith(".txt"):
            file_path = os.path.join(data_dir, fn)
            try:
                # Try UTF-8 first (most common)
                loader = TextLoader(file_path, encoding='utf-8')
                docs.extend(loader.load())
                print(f"Loaded {fn} with UTF-8 encoding")
            except UnicodeDecodeError:
                try:
                    # Try UTF-8 with error handling
                    loader = TextLoader(file_path, encoding='utf-8', autodetect_encoding=True)
                    docs.extend(loader.load())
                    print(f"Loaded {fn} with UTF-8 encoding (with error handling)")
                except Exception as e:
                    try:
                        # Try latin-1 as fallback (can decode any byte sequence)
                        loader = TextLoader(file_path, encoding='latin-1')
                        docs.extend(loader.load())
                        print(f"Loaded {fn} with latin-1 encoding")
                    except Exception as e2:
                        print(f"Failed to load {fn}: {e2}")
                        continue
            except Exception as e:
                print(f"Failed to load {fn}: {e}")
                continue
    
    if not docs:
        raise RuntimeError("No documents were successfully loaded!")
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=512, chunk_overlap=20)
    return splitter.split_documents(docs)

def populate_neo4j_with_chunks(chunks):
    ensure_ollama()                              # ← NEW
    embeddings = OllamaEmbeddings(model=EMBED_MODEL)
    Neo4jVector.from_documents(
        chunks, embeddings,
        url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD,
        index_name="dune_chunks", node_label="DuneChunk",
        embedding_node_property="embedding", text_node_property="text")
    print("Neo4j populated with document chunks.")

if __name__ == "__main__":
    os.makedirs("./data", exist_ok=True)
    with open("./data/dune_excerpt.txt", "w", encoding='utf-8') as f:
        f.write("The spice must flow…")
    chunks = load_and_chunk_documents()
    populate_neo4j_with_chunks(chunks)