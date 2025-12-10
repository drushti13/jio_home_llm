from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from chromadb import PersistentClient
import ollama
import time
import logging
import numpy as np
from datetime import datetime

embedding_cache = {}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("rag_logs.txt"),
        logging.StreamHandler()
    ]
)

CHROMA_DB_PATH = "chroma_db"
COLLECTION_NAME = "jio_chunks"

client = PersistentClient(path=CHROMA_DB_PATH)
collection = client.get_collection(name=COLLECTION_NAME)

class AskRequest(BaseModel):
    question: str
    top_k: int = 3
    detailed: bool = False

class AskResponse(BaseModel):
    answer: str
    sources: List[str]

app = FastAPI(title="Jio RAG API (Chroma + Ollama)", version="1.2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def embed_query(text: str):
    """Generate or reuse embedding for a query."""
    if text in embedding_cache:
        logging.info(f"Using cached embedding for: {text}")
        return embedding_cache[text]

    logging.info(f"--- New Query ---")
    logging.info(f"User question: {text}")

    t0 = time.perf_counter()
    resp = ollama.embed(model="nomic-embed-text", input=text)
    t1 = time.perf_counter()

    emb = resp["embeddings"][0]
    embedding_cache[text] = emb  # cache result

    logging.info(f"Embedding generated in {t1 - t0:.2f}s | Length={len(emb)}")
    logging.info(f"Embedding preview: {np.array(emb[:5])}...")
    return emb

def filter_for_apps(items):
    """
    Filters retrieved chunks to prioritize /apps pages if the query is about apps.
    If filtering removes everything, returns the original list.
    """
    filtered = [
        it for it in items
        if "/apps" in it["url"] or "/mobile/apps" in it["url"]
    ]
    if filtered:
        logging.info(f"Filtered to {len(filtered)} /apps-related chunks.")
    else:
        logging.info("No /apps URLs found; returning all results.")
    return filtered or items

def retrieve_top_k(question: str, top_k: int = 5):
    """Retrieve relevant chunks from Chroma with redundancy and keyword expansion."""
    logging.info(f"Retrieving up to {top_k} chunks for query: '{question}'")

    q_vec = embed_query(question)

    # Perform multiple retrieval passes (to ensure coverage)
    results = []
    all_ids = set()

    search_terms = [question]
    if "app" in question.lower():
        search_terms += ["Jio app", "apps", "Jio apps", "Jio application"]

    for term in search_terms:
        qv = embed_query(term)
        result = collection.query(query_embeddings=[qv], n_results=top_k)
        for i in range(len(result["documents"][0])):
            doc_id = result["ids"][0][i]
            if doc_id not in all_ids:
                all_ids.add(doc_id)
                meta = result["metadatas"][0][i] or {}
                items = {
                    "text": result["documents"][0][i],
                    "url": meta.get("url", ""),
                    "title": meta.get("title", ""),
                    "distance": result["distances"][0][i],
                }
                results.append(items)

    # Log what we got
    logging.info(f"Total unique chunks retrieved: {len(results)}")
    for i, r in enumerate(results[:15]):
        logging.info(f"[Chunk {i+1}] URL={r['url']} | Distance={r['distance']:.4f}")

    return results

def build_context(items, max_chars_per_chunk: int = 240) -> str:
    """Build text context from retrieved chunks."""
    parts = []
    for r in items:
        text = r["text"]
        if len(text) > max_chars_per_chunk:
            text = text[:max_chars_per_chunk] + "..."
        parts.append(
            f"URL: {r['url']}\n"
            f"Title: {r['title']}\n"
            f"Content:\n{text}\n\n---\n"
        )
    return "".join(parts)

def ask_llm(question: str, context: str, detailed: bool = False, model_name="llama3.2:3b") -> str:
    """Query Ollama LLM with the provided context and question."""
    if detailed:
        num_predict = 1024
        num_ctx = 4096
    else:
        num_predict = 300
        num_ctx = 1024


    logging.info(f"--- LLM Invocation ---")
    logging.info(f"Model: {model_name} | num_ctx={num_ctx} | num_predict={num_predict}")
    logging.info(f"--- Context Sent to LLM (truncated) ---")
    logging.info(context[:1000] + "..." if len(context) > 1000 else context)

    prompt = f"""
You are an assistant that answers questions ONLY using the website content below.

[WEBSITE CONTENT]
{context}

[USER QUESTION]
{question}

INSTRUCTIONS:
- Use ONLY the website content above to answer.
- DO NOT guess or invent any apps, products, features, or services.
- Every app, product, or service you list MUST appear by name in the website content.
- When the user asks to *list* items (like "list Jio apps" or "Jio services"):
    * Include all **major standalone apps** clearly mentioned in the context.
    * Ignore internal features, subsections, or utilities that are not full apps (like "My Photos", "MyJio subapps", or embedded tools).
    * If detailed mode is ON, expand each entry into multiple bullet points or sentences (4–6 lines total) that cover features, usage, and purpose.
- When the question asks *about one specific app*:
    * Give a rich answer — around 4–5 bullet points, highlighting all details found.
- End every valid answer with: "Sources: <list of URLs used>"
- If no relevant content is found, reply exactly:
  "I could not find this in the website data."
"""


    t0 = time.perf_counter()
    resp = ollama.chat(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        options={"num_ctx": num_ctx, "num_predict": num_predict},
    )
    t1 = time.perf_counter()

    answer = resp["message"]["content"].strip()
    logging.info(f"LLM completed in {t1 - t0:.2f}s")
    logging.info(f"LLM answer preview: {answer[:400]}...")
    return answer

@app.get("/")
def root():
    return {"message": "Jio RAG API running. Use POST /ask."}

@app.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest):
    """Main RAG endpoint with logging, retrieval, and LLM reasoning."""
    t_start = time.perf_counter()

    # Adaptive top_k and chunk size
    if payload.detailed:
        effective_top_k = max(payload.top_k, 4)
        max_chars = 500
    else:
        effective_top_k = min(payload.top_k, 2)
        max_chars = 250

    logging.info(f"Received request | Question='{payload.question}' | Detailed={payload.detailed} | top_k={payload.top_k}")

    # Step 1: Retrieval
    items = retrieve_top_k(payload.question, top_k=effective_top_k)

    # Step 2: Filter for /apps pages if relevant
    q_lower = payload.question.lower()
    if "app" in q_lower or "apps" in q_lower:
        items = filter_for_apps(items)
        logging.info("Applied /apps URL filter for app-related query.")

    # Step 3: Build LLM context
    context = build_context(items, max_chars_per_chunk=max_chars)

    t_mid = time.perf_counter()

    # Step 4: Get answer from LLM
    answer = ask_llm(
        question=payload.question,
        context=context,
        detailed=payload.detailed,
    )

    t_end = time.perf_counter()
    logging.info(f"[Timing] Retrieval+Context: {t_mid - t_start:.2f}s | LLM: {t_end - t_mid:.2f}s | Total: {t_end - t_start:.2f}s")

    source_urls = list({item["url"] for item in items if item["url"]})
    return AskResponse(answer=answer, sources=source_urls)
