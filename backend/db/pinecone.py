from pinecone import Pinecone
from core.config import get_settings
from functools import lru_cache


@lru_cache
def get_index():
    settings = get_settings()
    pc = Pinecone(api_key=settings.pinecone_api_key)
    return pc.Index(settings.pinecone_index)


def delete_namespace(namespace: str) -> None:
    try:
        get_index().delete(delete_all=True, namespace=namespace)
    except Exception:
        pass
