from langchain_ollama import OllamaLLM

llm = OllamaLLM(model="deepseek-r1")

response = llm.invoke("Who is Paul Atreides?")
print(response)
