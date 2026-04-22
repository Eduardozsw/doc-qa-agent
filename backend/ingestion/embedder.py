import os
import time
import tiktoken
from openai import OpenAI
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX", ""))

_enc = tiktoken.encoding_for_model("text-embedding-3-small")
_TPM_LIMIT = 950_000
_tokens_sent = 0
_window_start = time.time()

def _count_tokens(texts: list[str]) -> int:
    return sum(len(_enc.encode(t)) for t in texts)

def embed_text(text: str) -> list[float]:
    return embed_texts([text])[0]

def embed_texts(texts: list[str]) -> list[list[float]]:
    global _tokens_sent, _window_start

    token_count = _count_tokens(texts)
    elapsed = time.time() - _window_start

    if elapsed >= 60:
        _tokens_sent = 0
        _window_start = time.time()

    if _tokens_sent + token_count > _TPM_LIMIT:
        wait = 60 - elapsed
        time.sleep(wait)
        _tokens_sent = 0
        _window_start = time.time()

    response = client.embeddings.create(input=texts, model="text-embedding-3-small")
    _tokens_sent += token_count
    return [d.embedding for d in response.data]

def delete_namespace(namespace: str) -> None:
    try:
        index.delete(delete_all=True, namespace=namespace)
    except Exception:
        pass

UPSERT_BATCH_SIZE = 50
EMBED_BATCH_SIZE = 100

def upsert_chunks(chunks: list[tuple[str, int]], doc_name: str, namespace: str = "") -> None:
    vectors = []

    for batch_start in range(0, len(chunks), EMBED_BATCH_SIZE):
        batch = chunks[batch_start:batch_start + EMBED_BATCH_SIZE]
        texts = [text for text, _ in batch]
        embeddings = embed_texts(texts)
        for i, ((text, page), vetor) in enumerate(zip(batch, embeddings)):
            idx = batch_start + i
            vectors.append((f"{doc_name}_chunk_{idx}", vetor, {"text": text, "page": page}))

    for i in range(0, len(vectors), UPSERT_BATCH_SIZE):
        batch = vectors[i:i + UPSERT_BATCH_SIZE]
        index.upsert(vectors=batch, namespace=namespace)