from typing import cast
from pinecone import QueryResponse
from ingestion.embedder import embed_text, index
from concurrent.futures import ThreadPoolExecutor

def retrieve(query: str, top_k: int = 10, namespaces: list[str] = [""]) -> list[tuple[float, str, str, int]]:
    xq = embed_text(query)

    def retrieve_from_namespace(namespace: str) -> list[tuple[float, str, str, int]]:
        out = cast(QueryResponse, index.query(vector=xq, top_k=top_k, include_metadata=True, namespace=namespace))
        results = []
        for match in out.matches:
            text = match.metadata.get("text") if match.metadata else None
            if not text:
                continue
            page = int(match.metadata.get("page", 0)) if match.metadata else 0
            results.append((match.score, namespace, text, page))
        return results

    with ThreadPoolExecutor() as executor:
        results = list(executor.map(retrieve_from_namespace, namespaces))

    scored = sorted(
        [item for sublist in results for item in sublist],
        key=lambda x: x[0],
        reverse=True,
    )
    return scored