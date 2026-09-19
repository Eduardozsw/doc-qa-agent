"""Benchmark de ingestão: reindexa o PDF de demonstração num namespace isolado
(`bench_ingest`, apagado antes e depois) usando as funções reais do pipeline
(loader → chunker → contextualizer → embedder), medindo tempo, páginas/min e custo
de embedding."""
import time

from benchmark.cost import CostTracker
from benchmark.metrics import cost_usd, diff_usage
from core.config import get_settings

NAMESPACE_PADRAO = "bench_ingest"


def run(tracker: CostTracker, namespace: str = NAMESPACE_PADRAO) -> dict:
    from ingestion.chunker import chunk_pages
    from ingestion.contextualizer import build_preview, contextualize
    from ingestion.embedder import delete_namespace, upsert_chunks
    from ingestion.loader import load_pages_from_bytes
    from scripts.fetch_demo_pdf import DEMO_PDF_PATH, ensure_pdf

    if not DEMO_PDF_PATH.exists():
        ensure_pdf()
    contents = DEMO_PDF_PATH.read_bytes()

    delete_namespace(namespace)  # idempotente: garante namespace limpo antes de medir

    uso_antes = tracker.snapshot()
    t0 = time.perf_counter()

    pages = load_pages_from_bytes(contents)
    preview = build_preview("\n".join(text for _, text in pages))
    chunks = chunk_pages(pages)
    contexts = contextualize(chunks, preview)  # flag padrão desligada: não chama LLM
    upsert_chunks(chunks, namespace, namespace, contexts)

    tempo_total_s = time.perf_counter() - t0
    uso_depois = tracker.snapshot()
    uso_delta = diff_usage(uso_antes, uso_depois)

    delete_namespace(namespace)  # limpa depois também, para não deixar lixo no banco

    n_paginas = len(pages)
    paginas_por_min = n_paginas / (tempo_total_s / 60) if tempo_total_s > 0 else 0.0

    return {
        "namespace": namespace,
        "paginas": n_paginas,
        "chunks": len(chunks),
        "tempo_total_s": tempo_total_s,
        "paginas_por_min": paginas_por_min,
        "contextual_retrieval_enabled": get_settings().contextual_retrieval_enabled,
        "usage": uso_delta,
        "cost": cost_usd(uso_delta),
    }
