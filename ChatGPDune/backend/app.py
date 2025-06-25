from fastapi import FastAPI
from pydantic import BaseModel
from langchain_ollama import OllamaLLM
from fastapi.middleware.cors import CORSMiddleware
import re

app = FastAPI()

# Allow your frontend origin (adjust if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = OllamaLLM(model="deepseek-r1")

class Message(BaseModel):
    text: str

@app.post("/chat")
async def chat(message: Message):
    prompt = f"Answer clearly and directly with no internal reasoning. {message.text}"
    response = llm.invoke(prompt)
    reply_text = str(response)

    # Remove <think>...</think> blocks
    reply_text = re.sub(r"<think>.*?</think>", "", reply_text, flags=re.DOTALL).strip()

    return {"reply": reply_text}
