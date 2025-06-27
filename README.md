# Chat GPDune


tem que baixar o ollama pra rodar depois boto as intrucoes aqui   
https://ollama.com/download   

deixaram eu escolher entao a gente vai usar deepseek #CHINANUMBER1   
![image](https://github.com/user-attachments/assets/333f93f2-fb11-44db-be72-3658bf27643b)


dai roda isso   
```ollama pull deepseek-r1```   
```ollama run deepseek-r1```   

e ai da pra perguntar e ele roda local   
```where to find my ass?```   

e ele responde
![video](https://github.com/user-attachments/assets/fcdd00b6-2ae5-4d03-a2e1-3730a1a20d92)


tambem vai ter que baixar o neo4j desktop, rtodar um banco de dados e ai rodar aquele arquivo push data do python que ta la pra pppular o banco
depois eu atomiatico isso e a gente salva o banco direto aqui n ogit
![image](https://github.com/user-attachments/assets/5f4d223f-2176-442c-b839-70a0ee7e4c5a)



se quiser usar o frontend tem um readme dentro do /ChatGPDune explicando como faz


# como rodar:
- criar venv
- baixa tudo que ta no requirements
- baixa o ollama pelo site deles tem link ali em cima
- baixa o deepseek-r1 tem comando ali em cima
- nao precisa rodar ele, o programa roda sozinho
- segue as instrucoes pra rodar o frontend e pronto
- se nao quiser rodar o frontend ai so da pra usar via hard code pelo arquivo test_ollama


### todo list
- aumentar o banco de dados
- implementar Similarity Scores na rag e retriever para saber quando foi usada
- implementar um sistema de feedback de usuario
- salvar todas as mensagens que o usuario manda hehehe


-----------------------

Here’s a professional and clear `README.md` for your GitHub project:

---

# ChatGPDune

**ChatGPDune** is a **Dune-themed chatbot** powered by **Ollama** using the `deepseek-r1` LLM for conversation and **Neo4j** for retrieval-augmented generation (RAG). This project combines a stylish front-end, a fast Python backend, and a local knowledge graph to deliver immersive responses in the spirit of the Dune universe.

---

## 🏗️ Tech Stack

* **LLM**: [`deepseek-r1`](https://ollama.com/library/deepseek-r1) via [Ollama](https://ollama.com/)
* **RAG**: [Neo4j](https://neo4j.com/)
* **Backend**: FastAPI (Python)
* **Frontend**: React
* **Local setup**: Virtualenv, Node.js, Ollama

---

## 🚀 How to Run

### 1. Clone the project

```bash
git clone https://github.com/yourusername/ChatGPDune.git
cd ChatGPDune
```

### 2. Install Ollama

Download and install from: [https://ollama.com/download](https://ollama.com/download)

### 3. Pull the model

After installing Ollama, run:

```bash
ollama pull deepseek-r1
```

### 4. Set up the Python backend

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

# Install dependencies
pip install -r requirements.txt
```

### 5. Run the backend

In one terminal:

```bash
cd backend
uvicorn app:app --reload
```

### 6. Run the frontend

In another terminal:

```bash
cd frontend/chatgpdune
npm install  # only needed the first time
npm run start
```

---

## 🧠 Features

* 🐪 Dune-themed conversation style
* 🧠 Retrieval-Augmented Generation with Neo4j
* 🧾 Local LLM processing with deepseek-r1
* ⚡ FastAPI-powered backend
* 🎨 Modern frontend with React

