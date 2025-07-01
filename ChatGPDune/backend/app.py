from fastapi import FastAPI
from pydantic import BaseModel
from langchain_ollama import OllamaLLM
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Neo4jVector
from fastapi.middleware.cors import CORSMiddleware
import os
import re
import logging
from typing import List, Dict, Optional
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

# Available models configuration
AVAILABLE_MODELS = {
    "deepseek-r1": {
        "name": "DeepSeek R1",
        "model_id": "deepseek-r1",
        "description": "Advanced reasoning model",
        "remove_thinking": True  # This model uses thinking tags
    },
    # "llama3.2": {
    #     "name": "Llama 3.2",
    #     "model_id": "llama3.2",
    #     "description": "General purpose model",
    #     "remove_thinking": False
    # },
    # "qwen2.5": {
    #     "name": "Qwen 2.5",
    #     "model_id": "qwen2.5",
    #     "description": "Multilingual model",
    #     "remove_thinking": False
    # },
    # "mistral": {
    #     "name": "Mistral",
    #     "model_id": "mistral",
    #     "description": "Fast inference model",
    #     "remove_thinking": False
    # },
    # "phi3": {
    #     "name": "Phi 3",
    #     "model_id": "phi3",
    #     "description": "Compact efficient model",
    #     "remove_thinking": False
    # }
}

DEFAULT_MODEL = "deepseek-r1"

BASE_PROMPT = (
    "Your name is ChatGPDune."
    "You were created by Sortphy."
    "You are a chatbot based on the {model_name} model, ran locally with Ollama."
    "You are an expert on the Dune universe by Frank Herbert. "
    "Always answer questions strictly based on the Dune books and lore. "
    "Try to stick to the Dune theme and ChatGPDune info, but dont hesitate to answer questions about other topics if you can, but always try to answer them in a Dune way."
    "Give short answers, trying not to go over three sentences, unless the question requires more detail, then feel free to go over."
    "Be objective and factual, avoiding personal opinions or interpretations, unless you are asked for your personal opinion."
    "Be concise and to the point, focusing on the core of the question, if you can answer a question with few words, do it, do not extend yourself more than needed, unless you believe it's necessary."
    "If a question is unclear, ask for clarification.\n\n"
    "You can use markdown formatting (headers, lists, code blocks, etc.) when it would make your response clearer and more readable. Avoind using bold when not necessary."
    "If you feel that the user is being friendly, be friendly and engaging in your responses. You can use a bit of humor, but always keep it appropriate and relevant to the Dune universe and always be objetive and factual. You main priority is to answer the user's question.\n\n"
    "Use the following context from the Dune universe to answer the question:\n"
    "CONTEXT:\n{context}\n\n"
    "Question: {question}\n\n"
    "Answer based on the provided context:"
)

# novo base prompt que o chatgpt fez, se nao ficar bom a gente volta pro de cima que foi feito a mao
# OK ESSE NAO FICOU LEGAL OLHA ISSO KKKKKKKKK
# https://imgur.com/a/yvzlJiG
# BASE_PROMPT = (
#     "Your name is ChatGPDune.\n"
#     "You were created by Sortphy.\n"
#     "You run locally using the {model_name} model through Ollama.\n"
#     "You are deeply knowledgeable about the Dune universe by Frank Herbert — books, lore, factions, history, everything.\n"
#     "You always base your answers on canon sources from the Dune saga, avoiding fan theories unless explicitly asked.\n\n"

#     "You speak with clarity, confidence, and a touch of the mystique fitting of a mentat or Bene Gesserit.\n"
#     "Be friendly and engaging — people should enjoy talking to you. You're sharp, witty, and grounded in facts.\n"
#     "You can answer questions beyond Dune if needed, but whenever possible, flavor your responses with Dune-style insight, references, or metaphors. Make it feel like the spice flows through your words.\n\n"

#     "Keep your answers short and to the point — aim for 1 to 3 sentences. Go longer only when the question really calls for detail.\n"
#     "Avoid fluff or filler. Speak like someone who values silence, and only breaks it for truth.\n"
#     "If something’s unclear, don’t guess — ask for clarification.\n"
#     "You can use markdown for clarity (lists, headers, code blocks, etc.), but don’t overdo it. Avoid bold unless it adds real value.\n\n"

#     "Above all, be helpful, precise, and a little bit epic.\n\n"

#     "Use the following context from the Dune universe to answer the question:\n"
#     "CONTEXT:\n{context}\n\n"
#     "Question: {question}\n\n"
#     "Answer based on the provided context:"
# )



# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize embeddings (only one needed for vector search)
embeddings = OllamaEmbeddings(model=EMBED_MODEL)

# Initialize Neo4j vector store (this connects to your existing data)
vector_store = None

# Store LLM instances to avoid reinitializing
llm_instances = {}

def get_llm_instance(model_id: str) -> OllamaLLM:
    """Get or create LLM instance for the specified model"""
    if model_id not in llm_instances:
        if model_id not in AVAILABLE_MODELS:
            logger.warning(f"Unknown model {model_id}, using default {DEFAULT_MODEL}")
            model_id = DEFAULT_MODEL
        
        model_config = AVAILABLE_MODELS[model_id]
        llm_instances[model_id] = OllamaLLM(model=model_config["model_id"])
        logger.info(f"✓ Initialized LLM instance for {model_config['name']}")
    
    return llm_instances[model_id]

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

def process_model_response(response: str, model_id: str) -> str:
    """Process model response based on model-specific requirements"""
    model_config = AVAILABLE_MODELS.get(model_id, AVAILABLE_MODELS[DEFAULT_MODEL])
    
    # Remove thinking tags for models that use them (like DeepSeek R1)
    if model_config.get("remove_thinking", False):
        response = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL).strip()
    
    return response

class Message(BaseModel):
    text: str
    use_rag: bool = True
    model: Optional[str] = DEFAULT_MODEL  # Model selection

@app.on_event("startup")
async def startup_event():
    """Initialize vector store connection on startup"""
    if not initialize_vector_store():
        logger.warning("Failed to initialize vector store - RAG will not work properly")

@app.post("/chat")
async def chat(message: Message):
    try:
        # Validate and set model
        model_id = message.model if message.model in AVAILABLE_MODELS else DEFAULT_MODEL
        model_config = AVAILABLE_MODELS[model_id]
        
        # Check for the special "glauco" case
        if "glauco" in message.text.lower():
            return {
                "reply": "Glauco.",
                "model_used": model_id,
                "rag_used": False,
                "sources_used": 0
            }
        
        # Retrieve relevant context chunks - Skip retrieval if the user asked to disable RAG
        relevant_chunks = (
            retrieve_relevant_chunks(message.text, top_k=5)
            if message.use_rag else []
        )
        
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
        
        # Format the full prompt with context and model info
        full_prompt = BASE_PROMPT.format(
            model_name=model_config["name"],
            context=context,
            question=message.text
        )
        
        # Get LLM instance for the selected model
        llm = get_llm_instance(model_id)
        
        # Generate response using the selected LLM
        response = llm.invoke(full_prompt)
        reply_text = str(response)
        
        # Process response based on model requirements
        reply_text = process_model_response(reply_text, model_id)
        
        # Prepare response with metadata
        response_data = {
            "reply": reply_text,
            "model_used": model_id,
            "model_name": model_config["name"],
            "rag_used": bool(relevant_chunks),
            "sources_used": len(relevant_chunks)
        }

        # Add source information with actual content
        if relevant_chunks:
            sources = []
            for i, chunk in enumerate(relevant_chunks):  # Use same number as original (top 5 from retrieve_relevant_chunks)
                source_data = {
                    "id": i + 1,
                    "content": chunk["text"],
                    "score": round(chunk["score"], 4) if chunk.get("score") else None,
                    "preview": chunk["text"][:150] + "..." if len(chunk["text"]) > 150 else chunk["text"]
                }
                
                # Add metadata if available
                if chunk.get("metadata"):
                    source_file = chunk["metadata"].get("source_file", "Unknown")
                    source_type = chunk["metadata"].get("source_type", "local")
                    source_data["file"] = source_file
                    source_data["type"] = source_type
                else:
                    source_data["file"] = "Database chunk"
                    source_data["type"] = "unknown"
                
                sources.append(source_data)
            
            response_data["sources"] = sources
            
            # Keep the old format for backwards compatibility (showing top 3 as before)
            response_data["top_sources"] = []
            for chunk in relevant_chunks[:3]:  # Show top 3 sources as before
                if chunk.get("metadata"):
                    source_file = chunk["metadata"].get("source_file", "Unknown")
                    source_type = chunk["metadata"].get("source_type", "local")
                    response_data["top_sources"].append(f"{source_file} ({source_type})")
                else:
                    response_data["top_sources"].append("Database chunk")
        
        logger.info(f"Response generated using {model_config['name']} (RAG: {message.use_rag})")
        return response_data
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return {
            "reply": "I encountered an error processing your question. Please try again.",
            "model_used": message.model or DEFAULT_MODEL,
            "rag_used": False,
            "sources_used": 0
        }

@app.get("/models")
async def get_available_models():
    """Get list of available models"""
    return {
        "models": [
            {
                "id": model_id,
                "name": config["name"],
                "description": config["description"],
                "is_default": model_id == DEFAULT_MODEL
            }
            for model_id, config in AVAILABLE_MODELS.items()
        ],
        "default_model": DEFAULT_MODEL
    }

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
            "available_models": list(AVAILABLE_MODELS.keys()),
            "default_model": DEFAULT_MODEL,
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

# Test endpoint for model switching
@app.post("/test_model")
async def test_model(model_id: str, prompt: str = "Hello, introduce yourself briefly."):
    """Test endpoint to verify a model is working"""
    try:
        if model_id not in AVAILABLE_MODELS:
            return {"error": f"Model {model_id} not available"}
        
        llm = get_llm_instance(model_id)
        response = llm.invoke(prompt)
        processed_response = process_model_response(str(response), model_id)
        
        return {
            "model_id": model_id,
            "model_name": AVAILABLE_MODELS[model_id]["name"],
            "test_prompt": prompt,
            "response": processed_response,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error testing model {model_id}: {e}")
        return {
            "model_id": model_id,
            "error": str(e),
            "status": "error"
        }

# Cleanup on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    global vector_store, llm_instances
    if vector_store:
        vector_store = None
    llm_instances.clear()
    logger.info("Cleaned up resources")