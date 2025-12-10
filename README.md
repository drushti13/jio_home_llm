# 🚀 Jio RAG Assistant

A Retrieval-Augmented Generation (RAG) chatbot that scrapes Jio website content, stores embeddings in ChromaDB, and uses an LLM via Ollama to generate accurate, context-aware answers.


## 📌 Description
This project is an end-to-end RAG system built using **FastAPI**, **ChromaDB**, and **Ollama**.  
It scrapes Jio-related content, converts it into embeddings, stores them in a vector database, and retrieves the most relevant chunks at query time to produce intelligent, context-driven responses.

The frontend is a simple **HTML/CSS/JS**-based chat UI that connects to the FastAPI backend.


## ⭐ Features
- 🔍 Web scraper to extract Jio website data  
- 🧠 Embedding generation using Ollama  
- 📦 ChromaDB vector store for similarity search  
- 🤖 RAG-based FastAPI backend  
- 💬 Clean chat-based frontend (HTML + JS)  
- 🐳 Docker support for easy deployment  
- 📝 Logging for debugging and analytics  


## 🧱 Tech Stack
- **Backend:** FastAPI (Python)  
- **LLM & Embeddings:** Ollama  
- **Vector Database:** ChromaDB  
- **Frontend:** HTML, CSS, JavaScript  
- **Infrastructure:** Docker, Docker Compose  


## 🛠️ How to Run the Project 

Clone the repository
```bash
git clone https://github.com/drushti13/jio_home_llm
cd jio_home_llm
```
Install Python dependencies
```bash
pip install -r backend/requirements.txt
Build embeddings (ChromaDB index)
python backend/build_index.py
```
Run the FastAPI backend
```bash
uvicorn backend.main:app --reload
