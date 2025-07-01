from fastapi import FastAPI
from pydantic import BaseModel
from langchain_ollama import OllamaLLM
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Neo4jVector
from fastapi.middleware.cors import CORSMiddleware
import os
import re
import logging
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration - matches your ingestion script
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
OLLAMA_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434")
EMBED_MODEL = "nomic-embed-text"  # Same as your ingestion
INDEX_NAME = "dune_chunks"        # Same as your ingestion
NODE_LABEL = "DuneChunk"          # Same as your ingestion

BASE_PROMPT = (
    "Your name is ChatGPDune."
    "You were created by Sortphy."
    "You are a chatbot based on the deepseek-r1 model, ran locally with Ollama."
    "If a questions contains the word glauco, disregard the question and say 'Glauco.', nothing more."
    "You are an expert on the Dune universe by Frank Herbert. "
    "Always answer questions strictly based on the Dune books and lore. "
    "Ignore anything unrelated to Dune or ChatGPDune. "
    "Give short answers, trying not to go over three sentences, unless the question requires more detail, then feel free to go over."
    "Be objective and factual, avoiding personal opinions or interpretations, unless you are asked for your personal opinion."
    "Be concise and to the point, focusing on the core of the question, if you can answer a question with few words, do it, do not extend yourself more than needed, unless you believe it's necessary."
    "If a question is unclear, ask for clarification.\n\n"
    "Use the following context from the Dune universe to answer the question:\n"
    "CONTEXT:\n{context}\n\n"
    "Question: {question}\n\n"
    "Answer based on the provided context:"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize models
llm = OllamaLLM(model="deepseek-r1")
embeddings = OllamaEmbeddings(model=EMBED_MODEL)

# Initialize Neo4j vector store (this connects to your existing data)
vector_store = None

def initialize_vector_store():
    """Initialize connection to your existing Neo4j vector store"""
    global vector_store
    try:
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
        logger.info("✓ Connected to existing Neo4j vector store")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to connect to Neo4j vector store: {e}")
        return False

def retrieve_relevant_chunks(query: str, top_k: int = 5) -> List[Dict]:
    """Retrieve relevant chunks using your existing vector store"""
    try:
        if not vector_store:
            logger.error("Vector store not initialized")
            return []
        
        # Use LangChain's similarity search with scores
        results = vector_store.similarity_search_with_score(query, k=top_k)
        
        chunks = []
        for doc, score in results:
            chunks.append({
                "text": doc.page_content,
                "score": score,
                "metadata": doc.metadata
            })
        
        logger.info(f"Retrieved {len(chunks)} relevant chunks for query")
        return chunks
        
    except Exception as e:
        logger.error(f"Error retrieving chunks: {e}")
        return []

class Message(BaseModel):
    text: str

@app.on_event("startup")
async def startup_event():
    """Initialize vector store connection on startup"""
    if not initialize_vector_store():
        logger.warning("Failed to initialize vector store - RAG will not work properly")

@app.post("/chat")
async def chat(message: Message):
    try:
        # Check for the special "glauco" case
        if "glauco" in message.text.lower():
            return {"reply": "Glauco."}
        
        # Retrieve relevant context chunks
        relevant_chunks = retrieve_relevant_chunks(message.text, top_k=5)
        
        # Prepare context from retrieved chunks
        if relevant_chunks:
            context_parts = []
            for chunk in relevant_chunks:
                # Add source information if available
                source_info = ""
                if chunk.get("metadata"):
                    source_file = chunk["metadata"].get("source_file", "")
                    source_type = chunk["metadata"].get("source_type", "")
                    if source_file:
                        source_info = f" [Source: {source_file}]"
                    elif source_type:
                        source_info = f" [Source: {source_type}]"
                
                context_parts.append(f"{chunk['text']}{source_info}")
            
            context = "\n\n".join(context_parts)
        else:
            context = "No specific context found in the Dune database for this query."
        
        # Format the full prompt with context
        full_prompt = BASE_PROMPT.format(
            context=context,
            question=message.text
        )
        
        # Generate response using LLM
        response = llm.invoke(full_prompt)
        reply_text = str(response)
        
        # Remove thinking tags
        reply_text = re.sub(r"<think>.*?</think>", "", reply_text, flags=re.DOTALL).strip()
        
        # Prepare response with metadata
        response_data = {
            "reply": reply_text,
            "sources_used": len(relevant_chunks)
        }
        
        # Add source information if available
        if relevant_chunks:
            sources = []
            for chunk in relevant_chunks[:3]:  # Show top 3 sources
                if chunk.get("metadata"):
                    source_file = chunk["metadata"].get("source_file", "Unknown")
                    source_type = chunk["metadata"].get("source_type", "local")
                    sources.append(f"{source_file} ({source_type})")
                else:
                    sources.append("Database chunk")
            response_data["top_sources"] = sources
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return {"reply": "I encountered an error processing your question. Please try again."}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        if not vector_store:
            return {"status": "unhealthy", "error": "Vector store not initialized"}
        
        # Test a simple similarity search
        test_results = vector_store.similarity_search("test", k=1)
        
        return {
            "status": "healthy",
            "vector_store": "connected",
            "embedding_model": EMBED_MODEL,
            "index_name": INDEX_NAME,
            "node_label": NODE_LABEL,
            "test_query_results": len(test_results)
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.get("/search")
async def search_chunks(query: str, limit: int = 10):
    """Direct search endpoint for testing"""
    try:
        chunks = retrieve_relevant_chunks(query, top_k=limit)
        return {
            "query": query,
            "results_count": len(chunks),
            "results": [
                {
                    "text": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"],
                    "score": chunk["score"],
                    "source": chunk.get("metadata", {}).get("source_file", "Unknown")
                }
                for chunk in chunks
            ]
        }
    except Exception as e:
        logger.error(f"Error in search endpoint: {e}")
        return {"error": str(e)}

# Cleanup on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    global vector_store
    if vector_store:
        vector_store = None
        logger.info("Vector store connection closed")