# ChatGPDune
### Dune themed RAG based LLM ChatBot. | Using Ollama, DeepSeek, Neo4J and LangChain


#### Grupo: Gustavo Henrique, Icaro Botelho, Maruan Biasi, Mauricio Nunes

-------------------------------

# To run:

## Ollama Setup:
- Install Ollama from https://ollama.com/download
- Pull whatever model you want to use, by default the project uses only deepseek-r1, you can pull it using the following command:
- ```pull deepseek-r1:latest```

## Neo4j Setup:
- Install neo4j desktop from https://neo4j.com/download/
- Open Neo4j desktop and create a database, preferably called chatgpdune
- When creating the database, make sure to add your user and password to the .env

## Project Setup
- clone git repo
- create and activate venv via ```python -m venv venv```
- install python requirements via ```pip install -r requirements.txt```

## Database Setup
- you need a populated database to use the RAG
- the easiest way is to import the pre-processed embeddings from the Dune 1 book using the csv file
- open neo4j desktop, connect to the database and import the file located inside our project at /database/Ingested/book-1-only/node-export.csv
- This csv file contains all embeddings from the Dune 1 book, which would take hours to process.
- If you want more data inside you database, which is recommended, follow the tutorial below on how to process data locally.

## Run Backend
- from project root do the following
- ```cd backend```
- ```uvicorn app:app --reload```

## Run Frontend
- from project root do the following
- ```cd frontend/chatgpdune```
- ```npm i```
- ```npm run start```

## (Optional) How to process data locally for the RAG
- To process data locally, which is basically generate the embeddings for chunks of text using your own machine, do the following
- Pull the nomic-embed-text model via ollama using ```ollama pull nomic-embed-text```
- ```cd RAG```
- Everything inside the "data" folder will be processed and it's embeddings will the added to the database.
- If you want to ignore a file, which means, skip it's embeddings, you can put it inside /data/ignore. All other children folders inside /data will be processed, only /data/ignore wont.
- It supports the following file formats: [.txt, .pdf, .html, .htm, .md, .markdown]
- It also does webscraping from the dune fandom wiki, you can choose to turn this feature on or off when you run the data ingestion system.
- Inside the file "data_ingestion.py" you can customize different parameters on the "Tweakable settings" section.
- On line 294, you can customize how many wiki pages to scrape.
- To run the data ingestion system, use the following command: ```python data_ingestion.py```
