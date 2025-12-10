import json
import ollama
from chromadb import PersistentClient

SCRAPED_JSON = "jio_scraped_bs4.jsonl"
CHROMA_DB_PATH = "chroma_db"
COLLECTION_NAME = "jio_chunks"

# ---- Create Chroma client (NEW SYNTAX) ----
client = PersistentClient(path=CHROMA_DB_PATH)

# Remove old collection if it exists
if COLLECTION_NAME in [c.name for c in client.list_collections()]:
    client.delete_collection(name=COLLECTION_NAME)

collection = client.create_collection(name=COLLECTION_NAME)

# ---- Helpers ----

def load_scraped_data(path):
    pages = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                pages.append(json.loads(line))
    return pages

def chunk_text(text, chunk_size=500, overlap=100):
    text = text.strip()
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

def embed_text(text):
    resp = ollama.embed(model="nomic-embed-text", input=text)
    return resp["embeddings"][0]

# ---- Main ----

def main():
    pages = load_scraped_data(SCRAPED_JSON)
    print(f"Loaded {len(pages)} pages")

    chunk_id = 0

    for page in pages:
        text = page.get("text", "").strip()
        if not text:
            continue

        url = page.get("url", "")
        title = page.get("title", "")

        chunks = chunk_text(text)

        for chunk in chunks:
            print(f"Embedding chunk {chunk_id}...", end="\r")
            emb = embed_text(chunk)

            collection.add(
                ids=[f"chunk_{chunk_id}"],
                embeddings=[emb],
                documents=[chunk],
                metadatas=[{"url": url, "title": title}]
            )

            chunk_id += 1

    print(f"Inserted {chunk_id} chunks into ChromaDB.")

if __name__ == "__main__":
    main()
