"""Aplica as flags de ablação via variável de ambiente + `get_settings.cache_clear()`,
restaurando o ambiente ao sair — nunca escreve em `.env`.
"""
import os
from contextlib import contextmanager

from core.config import get_settings

# MODEL_ROUTING_ENABLED e cache semântico ficam desligados em TODAS as configs: o
# benchmark mede o pipeline determinístico de recuperação/geração, não o roteador de
# modelo (F6) nem hits de cache (medido à parte, ver cache_bench.py).
COMMON_ENV = {"MODEL_ROUTING_ENABLED": "false", "SEMANTIC_CACHE_ENABLED": "false"}

CONFIGS: dict[str, dict[str, str]] = {
    "naive": {"HYBRID_SEARCH": "false", "RERANK_ENABLED": "false", "MULTI_QUERY_ENABLED": "false"},
    "hybrid": {"HYBRID_SEARCH": "true", "RERANK_ENABLED": "false", "MULTI_QUERY_ENABLED": "false"},
    "full": {"HYBRID_SEARCH": "true", "RERANK_ENABLED": "true", "MULTI_QUERY_ENABLED": "true"},
}


@contextmanager
def apply_config(nome: str):
    """Define as env vars da config `nome` (+ COMMON_ENV), limpa o cache de
    `get_settings()`, roda o bloco, e restaura o ambiente anterior ao sair (mesmo em
    caso de exceção) — sem isso, uma falha no meio deixaria o processo com flags
    trocadas para o resto da execução."""
    env = {**COMMON_ENV, **CONFIGS[nome]}
    anteriores = {chave: os.environ.get(chave) for chave in env}

    try:
        os.environ.update(env)
        get_settings.cache_clear()
        yield get_settings()
    finally:
        for chave, valor in anteriores.items():
            if valor is None:
                os.environ.pop(chave, None)
            else:
                os.environ[chave] = valor
        get_settings.cache_clear()
