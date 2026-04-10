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

def upsert_chunks(chunks: list[str], doc_name: str) -> None:
    vectors = []
    
    for i, chunk in enumerate(chunks):
        vetor = embed_text(chunk)
        id = f"{doc_name}_chunk_{i}"
        metadata = {"text": chunk}
        vectors.append((id, vetor, metadata))
    index.upsert(vectors=vectors)