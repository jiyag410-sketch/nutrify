import json
from sentence_transformers import SentenceTransformer
import chromadb

# Load processed chunks
with open("data/processed_chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

print(f"Loaded {len(chunks)} chunks")

# Load embedding model (small, fast, free, runs locally)
print("Loading embedding model...")
model = SentenceTransformer("all-MiniLM-L6-v2")

# Set up Chroma (persistent local vector database)
client = chromadb.PersistentClient(path="./vectorstore")
collection = client.get_or_create_collection(name="health_nutrition")

# Prepare data for insertion
texts = [chunk["text"] for chunk in chunks]
ids = [str(i) for i in range(len(chunks))]
metadatas = [{"source": chunk["source"]} for chunk in chunks]

# Embed in batches (faster, avoids memory issues)
batch_size = 100
print("Embedding and storing chunks...")

for i in range(0, len(texts), batch_size):
    batch_texts = texts[i:i+batch_size]
    batch_ids = ids[i:i+batch_size]
    batch_metadatas = metadatas[i:i+batch_size]

    embeddings = model.encode(batch_texts).tolist()

    collection.add(
        ids=batch_ids,
        embeddings=embeddings,
        documents=batch_texts,
        metadatas=batch_metadatas
    )

    print(f"Processed {min(i+batch_size, len(texts))}/{len(texts)} chunks")

print("Vector store built successfully!")
print(f"Total items in collection: {collection.count()}")
