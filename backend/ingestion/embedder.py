import os
from openai import OpenAI
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX", ""))

def embed_text(text:str) -> list[float]:
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )

    return response.data[0].embedding

def delete_namespace(namespace: str) -> None:
    try:
        index.delete(delete_all=True, namespace=namespace)
    except Exception:
        pass

UPSERT_BATCH_SIZE = 50

def upsert_chunks(chunks: list[str], doc_name: str, namespace: str = "") -> None:
    vectors = []

    for i, chunk in enumerate(chunks):
        vetor = embed_text(chunk)
        vectors.append((f"{doc_name}_chunk_{i}", vetor, {"text": chunk}))

    for i in range(0, len(vectors), UPSERT_BATCH_SIZE):
        batch = vectors[i:i + UPSERT_BATCH_SIZE]
        index.upsert(vectors=batch, namespace=namespace)