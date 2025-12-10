📌 Jio RAG Assistant (Retrieval Augmented Generation App)

A custom-built RAG application that scrapes Jio-related content, stores embeddings in ChromaDB, and answers user queries using an LLM (Ollama or any model you choose).

🚀 Features

🔍 Web Scraper — Scrapes Jio websites & saves JSONL

🧠 Embeddings Engine — Uses Ollama embeddings + ChromaDB

💬 RAG Chatbot — Answers user questions using retrieved context

🖥️ Frontend Interface — Simple HTML/CSS/JS

🗂️ Backend API — FastAPI with clean routes

🐳 Docker-ready — Run anywhere with docker-compose

⚙️ Setup & Installation
1. Clone the repo
git clone https://github.com/drushti13/jio_home_llm
cd jio_home_llm

2. Create environment variables

Inside backend/.env.example, duplicate and rename it:

cp backend/.env.example backend/.env


Add your values:

OLLAMA_HOST=http://localhost:11434
CHROMA_DB_PATH=./chroma_db
API_PORT=8000

🧠 Build Embeddings

Run the script to process scraped files and store embeddings in ChromaDB:

python backend/build_index.py

▶️ Run the Backend
uvicorn backend.main:app --reload

🌐 Run the Frontend

Simply open:

frontend/index.html


Or serve it using any static server plugin.

🐳 Run Entire App with Docker
docker-compose up --build
