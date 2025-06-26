from fastapi import FastAPI
from pydantic import BaseModel
from langchain_ollama import OllamaLLM
from fastapi.middleware.cors import CORSMiddleware
import re

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

class Message(BaseModel):
    text: str

@app.post("/chat")
async def chat(message: Message):

    full_prompt = BASE_PROMPT.format(question=message.text)

    response = llm.invoke(full_prompt)

    reply_text = str(response)

    # Remove <think>...</think> blocks
    reply_text = re.sub(r"<think>.*?</think>", "", reply_text, flags=re.DOTALL).strip()

    return {"reply": reply_text}
