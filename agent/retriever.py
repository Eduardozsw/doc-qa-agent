from typing import cast
from pinecone import QueryResponse
from ingestion.embedder import embed_text, index
from concurrent.futures import ThreadPoolExecutor

def retrieve(query: str, top_k: int = 20, namespaces: list[str] = [""]) -> list[tuple[str, str]]:
    xq = embed_text(query)

    def retrieve_from_namespace(namespace: str) -> list[tuple[float, str, str]]:
        out = cast(QueryResponse, index.query(vector=xq, top_k=top_k, include_metadata=True, namespace=namespace))
        return [(match.score, namespace, match.metadata["text"]) for match in out.matches]

    with ThreadPoolExecutor() as executor:
        results = list(executor.map(retrieve_from_namespace, namespaces))

    scored = sorted(
        [item for sublist in results for item in sublist],
        key=lambda x: x[0],
        reverse=True,
    )
    return [(namespace, text) for _, namespace, text in scored]