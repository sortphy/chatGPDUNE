from fastapi import FastAPI
from pydantic import BaseModel
from langchain_ollama import OllamaLLM
from fastapi.middleware.cors import CORSMiddleware

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
    response = llm(message.text)
    return {"reply": response}
