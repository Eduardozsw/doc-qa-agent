from typing import cast
from pinecone import QueryResponse
from ingestion.embedder import embed_text, index

def retrieve(query:str, top_k: int = 3) -> list[str]:
    xq = embed_text(query)
    out = cast(QueryResponse, index.query(vector= xq, top_k = top_k, include_metadata=True))

    return [match.metadata["text"] for match in out.matches]