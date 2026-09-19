"""Benchmark do cache semântico: para cada pergunta, mede a latência de uma chamada
fria (`use_cache=True`, sem nada em cache) e a repetição imediata (deve dar hit).
Invalida o cache do namespace antes e depois para partir de estado limpo e não
deixar entradas obsoletas para trás."""
import os
import time

from core.config import get_settings
from db import query_cache as query_cache_db


def run(namespace: str, queries: list[str]) -> list[dict]:
    from agent.orchestrator import orchestrator

    # Força o cache semântico ligado (o loop de ablação o desliga via env), restaura
    # o valor anterior ao sair — este benchmark roda depois das configs de ablação.
    anterior = os.environ.get("SEMANTIC_CACHE_ENABLED")
    os.environ["SEMANTIC_CACHE_ENABLED"] = "true"
    get_settings.cache_clear()

    query_cache_db.invalidate_namespace(namespace)
    resultados = []

    try:
        for query in queries:
            t0 = time.perf_counter()
            orchestrator(query, namespaces=[namespace], plan="pro", use_cache=True)
            tempo_frio_ms = (time.perf_counter() - t0) * 1000

            t0 = time.perf_counter()
            resultado = orchestrator(query, namespaces=[namespace], plan="pro", use_cache=True)
            tempo_hit_ms = (time.perf_counter() - t0) * 1000

            resultados.append({
                "query": query,
                "cold_ms": tempo_frio_ms,
                "hit_ms": tempo_hit_ms,
                "cache_hit_confirmado": bool(resultado.get("cached")),
            })
    finally:
        query_cache_db.invalidate_namespace(namespace)
        if anterior is None:
            os.environ.pop("SEMANTIC_CACHE_ENABLED", None)
        else:
            os.environ["SEMANTIC_CACHE_ENABLED"] = anterior
        get_settings.cache_clear()

    return resultados
