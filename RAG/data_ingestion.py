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
        return                  # It’s running – nothing to do.
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
            docs.extend(TextLoader(os.path.join(data_dir, fn)).load())
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
    with open("./data/dune_excerpt.txt", "w") as f:
        f.write("The spice must flow…")
    chunks = load_and_chunk_documents()
    populate_neo4j_with_chunks(chunks)
