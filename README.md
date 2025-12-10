# Jio RAG Assistant

A retrieval-augmented chatbot that scrapes the Jio website, embeds content with Ollama embeddings, stores chunks in ChromaDB, and answers questions via an Ollama LLM.  
Frontend: simple SPA in `frontend/` that talks to the FastAPI backend.  

## Key files
- `backend/main.py` — FastAPI app and RAG flow. :contentReference[oaicite:12]{index=12}  
- `backend/build_index.py` — scrapes / loads jsonl and uploads embeddings to ChromaDB. :contentReference[oaicite:13]{index=13}  
- `backend/web_scraper.py` — the website scraper. :contentReference[oaicite:14]{index=14}  
- `frontend/` — `index.html`, `style.css`, `script.js`. :contentReference[oaicite:15]{index=15} :contentReference[oaicite:16]{index=16} :contentReference[oaicite:17]{index=17}

## Quick local dev (recommended)
1. Create `.env` from `.env.example` and set values (OLLAMA_HOST etc).
2. Build and run with Docker Compose:
```bash
docker-compose up --build
