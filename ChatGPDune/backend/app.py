import sys
import os
import re
from collections import Counter

# Add the root directory to the Python path to access RAG module
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI
from pydantic import BaseModel
from langchain_ollama import OllamaLLM
from fastapi.middleware.cors import CORSMiddleware
from langchain_community.llms import Ollama
from langchain.chains import RetrievalQA
from dotenv import load_dotenv

from RAG.retriever import get_neo4j_retriever

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

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize LLM
llm = OllamaLLM(model="deepseek-r1")

# RAG relevance detection functions
def has_substantial_content(docs, min_content_length=50):
    """
    Approach 1: Check if retrieved documents have substantial content
    """
    if not docs:
        return False, []  # Return tuple even when no docs
    
    substantial_docs = []
    for doc in docs:
        if len(doc.page_content.strip()) >= min_content_length:
            substantial_docs.append(doc)
    
    return len(substantial_docs) > 0, substantial_docs

def is_context_relevant(question, context, min_overlap=0.2):
    """
    Approach 3: Check if the retrieved context is relevant to the question
    based on keyword overlap and content analysis
    """
    if not context or len(context.strip()) < 20:
        return False
    
    # Extract meaningful words from question (remove common words)
    stop_words = {
        'the', 'is', 'are', 'was', 'were', 'a', 'an', 'and', 'or', 'but', 
        'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'what', 'who', 
        'where', 'when', 'why', 'how', 'do', 'does', 'did', 'will', 'would', 
        'could', 'should', 'can', 'may', 'might', 'have', 'has', 'had'
    }
    
    question_words = set(re.findall(r'\b\w+\b', question.lower()))
    question_words = question_words - stop_words
    
    context_words = set(re.findall(r'\b\w+\b', context.lower()))
    
    # Calculate overlap
    if not question_words:
        return False
        
    overlap = len(question_words.intersection(context_words))
    overlap_ratio = overlap / len(question_words)
    
    return overlap_ratio >= min_overlap

def check_non_dune_keywords(question):
    """
    Additional check for common non-Dune questions that shouldn't use RAG
    """
    non_dune_patterns = [
        r'\b(what is your name|who are you|what are you)\b',
        r'\b(your name|tell me about yourself)\b',
        r'\b(who created you|who made you)\b',
        r'\b(what can you do|what do you do)\b'
    ]
    
    question_lower = question.lower()
    for pattern in non_dune_patterns:
        if re.search(pattern, question_lower):
            return True
    return False

# Initialize RAG components
try:
    retriever = get_neo4j_retriever()
    qa_chain = RetrievalQA.from_chain_type(
        llm=Ollama(model="deepseek-r1"),
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
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
            # Get relevant context from the retriever (using invoke instead of deprecated method)
            docs = retriever.invoke(message.text)
            print(f"DEBUG: Query: '{message.text}'")
            print(f"DEBUG: Retrieved {len(docs)} documents")
            
            # Let's also test with a direct similarity search to see if there's an issue with invoke
            try:
                # Try to access the underlying vectorstore for debugging
                vectorstore = retriever.vectorstore if hasattr(retriever, 'vectorstore') else None
                if vectorstore:
                    test_docs = vectorstore.similarity_search(message.text, k=3)
                    print(f"DEBUG: Direct similarity_search returned {len(test_docs)} documents")
                    if test_docs:
                        print(f"DEBUG: First doc preview: {test_docs[0].page_content[:100]}...")
            except Exception as debug_e:
                print(f"DEBUG: Error testing direct search: {debug_e}")
            
            if docs:
                print(f"DEBUG: First doc type: {type(docs[0])}")
                print(f"DEBUG: First doc preview: {docs[0].page_content[:100]}...")
            else:
                print("DEBUG: No documents found - possible retriever configuration issue")
            
            # Approach 1: Check if documents have substantial content
            result = has_substantial_content(docs)
            print(f"DEBUG: has_substantial_content returned: {result}, type: {type(result)}")
            
            has_content, substantial_docs = result
            
            # Early exit if no substantial content
            if not has_content:
                print(f"RAG: No substantial content found for: '{message.text[:50]}...'")
                full_prompt = BASE_PROMPT.format(context="", question=message.text)
                response = llm.invoke(full_prompt)
                reply_text = str(response)
                reply_text = re.sub(r"<think>.*?</think>", "", reply_text, flags=re.DOTALL).strip()
                
                return {
                    "reply": reply_text,
                    "sources": [],
                    "rag_used": False
                }
            
            # Create context from substantial documents
            context = "\n".join([doc.page_content for doc in substantial_docs[:3]])
            
            # Approach 3: Check keyword relevance
            is_relevant = is_context_relevant(message.text, context)
            
            # Additional check for non-Dune questions
            is_non_dune = check_non_dune_keywords(message.text)
            
            # Final decision: RAG is useful if content is substantial AND relevant AND not a non-Dune question
            rag_was_useful = has_content and is_relevant and not is_non_dune
            
            if rag_was_useful:
                full_prompt = BASE_PROMPT.format(context=context, question=message.text)
                source_info = [
                    {"content": doc.page_content[:200] + "...", "metadata": doc.metadata} 
                    for doc in substantial_docs[:2]
                ]
                print(f"RAG: Content deemed useful for: '{message.text[:50]}...'")
            else:
                # Use empty context
                full_prompt = BASE_PROMPT.format(context="", question=message.text)
                source_info = []
                reason = "non-Dune question" if is_non_dune else "low relevance"
                print(f"RAG: Content deemed not useful ({reason}) for: '{message.text[:50]}...'")
            
            # Get response from LLM
            response = llm.invoke(full_prompt)
            reply_text = str(response)
            
            # Remove thinking tags
            reply_text = re.sub(r"<think>.*?</think>", "", reply_text, flags=re.DOTALL).strip()
            
            return {
                "reply": reply_text,
                "sources": source_info if rag_was_useful else [],
                "rag_used": rag_was_useful
            }
        else:
            # Fallback to original functionality if RAG is not available
            full_prompt = BASE_PROMPT.format(context="", question=message.text)
            response = llm.invoke(full_prompt)
            reply_text = str(response)
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

# Keep your existing endpoints
@app.get("/rag-status")
async def rag_status():
    return {
        "rag_enabled": rag_enabled,
        "retriever_available": retriever is not None if rag_enabled else False
    }

@app.post("/chat-rag")
async def chat_with_rag_only(message: Message):
    if not rag_enabled:
        return {"error": "RAG system not available"}
    
    if "glauco" in message.text.lower():
        return {"reply": "Glauco.", "rag_used": False}
    
    try:
        response = qa_chain.invoke({"query": message.text})
        reply_text = str(response["result"])
        
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