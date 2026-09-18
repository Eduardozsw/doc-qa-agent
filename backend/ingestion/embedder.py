import time
from functools import lru_cache

import tiktoken
from openai import OpenAI

from core.tracing import openai_client
from db import vectors as vectors_db

EMBED_BATCH_SIZE = 100

_TPM_LIMIT = 950_000
_tokens_sent = 0
_window_start = time.time()


@lru_cache
def _client() -> OpenAI:
    return openai_client()


@lru_cache
def _enc():
    return tiktoken.encoding_for_model("text-embedding-3-small")


def _count_tokens(texts: list[str]) -> int:
    return sum(len(_enc().encode(t)) for t in texts)


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

    response = _client().embeddings.create(input=texts, model="text-embedding-3-small")
    _tokens_sent += token_count
    return [d.embedding for d in response.data]


def delete_namespace(namespace: str) -> None:
    vectors_db.delete_namespace(namespace)


def upsert_chunks(chunks: list[tuple[str, int]], doc_name: str, namespace: str = "") -> None:
    for batch_start in range(0, len(chunks), EMBED_BATCH_SIZE):
        batch = chunks[batch_start:batch_start + EMBED_BATCH_SIZE]
        texts = [text for text, _ in batch]
        embeddings = embed_texts(texts)

        rows = []
        for i, ((text, page), vetor) in enumerate(zip(batch, embeddings)):
            idx = batch_start + i
            rows.append((f"{doc_name}_chunk_{idx}", idx, page, text, vetor))

        vectors_db.upsert_vectors(namespace, rows)
