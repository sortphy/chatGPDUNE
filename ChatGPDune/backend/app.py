import sys
import os
# Add the root directory to the Python path to access RAG module
# Go up two levels: backend -> ChatGPDune -> root
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI
from pydantic import BaseModel
from langchain_ollama import OllamaLLM
from fastapi.middleware.cors import CORSMiddleware
import re
from langchain_community.llms import Ollama
from langchain.chains import RetrievalQA
from dotenv import load_dotenv

from RAG.retriever import get_neo4j_retriever # Import the retriever function

load_dotenv()

app = FastAPI()

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
    "Context from Dune knowledge base: {context}\n\n"
    "Question: {question}"
)

# CORS PRA LIBERAR O FRONT PRA ENTRAR NO BACK
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# AQUI DEFINE QUAL MODELO OLLAMA VAI USAR, DEEPSEEK-R1 E TOP MAS PESADO QUALQUER COISA A GENTE MUDA PRA UM MAIS LEVE
# OU SE QUISER TEM AS VERSOES MAIS PESADAS DO DEEPSEEK MAS AI VAI FUDER TUDO PRA RODAR
llm = OllamaLLM(model="deepseek-r1")

# Initialize RAG components
try:
    retriever = get_neo4j_retriever()
    # Create a RetrievalQA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=Ollama(model="deepseek-r1"),  # Using Ollama for the chain
        chain_type="stuff",  # Other options: "map_reduce", "refine", "map_rerank"
        retriever=retriever,
        return_source_documents=True  # To see which documents were used
    )
    rag_enabled = True
    print("RAG system initialized successfully")
except Exception as e:
    print(f"Failed to initialize RAG system: {e}")
    rag_enabled = False

class Message(BaseModel):
    text: str

@app.post("/chat")
async def chat(message: Message):
    # Check for the special "glauco" condition first
    if "glauco" in message.text.lower():
        return {"reply": "Glauco.", "rag_used": False}
    
    try:
        if rag_enabled:
            # Use RAG-enhanced response
            # Get relevant context from the retriever
            docs = retriever.get_relevant_documents(message.text)
            context = "\n".join([doc.page_content for doc in docs[:3]])  # Use top 3 most relevant docs
            
            # Format the prompt with context
            full_prompt = BASE_PROMPT.format(context=context, question=message.text)
            
            # Get response from LLM
            response = llm.invoke(full_prompt)
            reply_text = str(response)
            
            # APAGAR OS <think>...</think> PRA NAO MOSTRAR O PENSAMENTO DA LLM NO FRONT
            reply_text = re.sub(r"<think>.*?</think>", "", reply_text, flags=re.DOTALL).strip()
            
            # Get source documents for reference (optional)
            source_info = [{"content": doc.page_content[:200] + "...", "metadata": doc.metadata} for doc in docs[:2]]
            
            return {
                "reply": reply_text,
                "sources": source_info,  # Optional: include source information
                "rag_used": True
            }
        else:
            # Fallback to original functionality if RAG is not available
            full_prompt = BASE_PROMPT.format(context="", question=message.text)
            response = llm.invoke(full_prompt)
            reply_text = str(response)
            
            # APAGAR OS <think>...</think> PRA NAO MOSTRAR O PENSAMENTO DA LLM NO FRONT
            reply_text = re.sub(r"<think>...</think>", "", reply_text, flags=re.DOTALL).strip()
            
            return {
                "reply": reply_text,
                "rag_used": False
            }
            
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        # Fallback to basic response in case of any error
        full_prompt = BASE_PROMPT.format(context="", question=message.text)
        response = llm.invoke(full_prompt)
        reply_text = str(response)
        reply_text = re.sub(r"<think>.*?</think>", "", reply_text, flags=re.DOTALL).strip()
        
        return {
            "reply": reply_text,
            "error": "RAG system temporarily unavailable",
            "rag_used": False
        }

# Optional: Add an endpoint to check RAG system status
@app.get("/rag-status")
async def rag_status():
    return {
        "rag_enabled": rag_enabled,
        "retriever_available": retriever is not None if rag_enabled else False
    }

# Optional: Add an endpoint for RAG-only responses (without fallback)
@app.post("/chat-rag")
async def chat_with_rag_only(message: Message):
    if not rag_enabled:
        return {"error": "RAG system not available"}
    
    # Check for the special "glauco" condition first
    if "glauco" in message.text.lower():
        return {"reply": "Glauco.", "rag_used": False}
    
    try:
        response = qa_chain.invoke({"query": message.text})
        reply_text = str(response["result"])
        
        # APAGAR OS <think>...</think> PRA NAO MOSTRAR O PENSAMENTO DA LLM NO FRONT
        reply_text = re.sub(r"<think>.*?</think>", "", reply_text, flags=re.DOTALL).strip()
        
        return {
            "reply": reply_text,
            "source_documents": [
                {"content": doc.page_content[:200] + "...", "metadata": doc.metadata} 
                for doc in response["source_documents"]
            ]
        }
    except Exception as e:
        return {"error": f"RAG query failed: {str(e)}"}