from concurrent.futures import ThreadPoolExecutor

from db import vectors as vectors_db
from ingestion.embedder import embed_text


def retrieve(query: str, top_k: int = 10, namespaces: list[str] = [""]) -> list[tuple[float, str, str, int]]:
    xq = embed_text(query)

    def retrieve_from_namespace(namespace: str) -> list[tuple[float, str, str, int]]:
        matches = vectors_db.query(namespace, xq, top_k)
        return [(score, namespace, text, page) for score, text, page in matches]

    with ThreadPoolExecutor() as executor:
        results = list(executor.map(retrieve_from_namespace, namespaces))

    scored = sorted(
        [item for sublist in results for item in sublist],
        key=lambda x: x[0],
        reverse=True,
    )
    return scored
