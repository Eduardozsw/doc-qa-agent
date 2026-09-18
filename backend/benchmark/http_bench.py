"""Benchmark HTTP ponta a ponta (opcional, `--http-url`): login com o usuário demo
(credenciais de `get_settings()`), descobre o namespace do PDF demo via
`GET /api/ingest`, e mede time-to-first-token + tempo total de
`POST /api/query/stream` para até `--http-n` perguntas, respeitando o limite de
5 req/min do endpoint (dorme entre requisições)."""
import json
import time

import httpx

from core.config import get_settings

RATE_LIMIT_SLEEP_S = 13  # limite é 5/min (1 a cada 12s); 13s de folga


def _login(client: httpx.Client, base_url: str) -> str:
    settings = get_settings()
    resposta = client.post(
        f"{base_url}/api/auth/login",
        json={"email": settings.demo_user_email, "password": settings.demo_user_password},
    )
    resposta.raise_for_status()
    return resposta.json()["access_token"]


def _descobrir_namespace_demo(client: httpx.Client, base_url: str, token: str) -> str | None:
    resposta = client.get(f"{base_url}/api/ingest", headers={"Authorization": f"Bearer {token}"})
    resposta.raise_for_status()
    arquivos = resposta.json().get("arquivos", [])
    return arquivos[0] if arquivos else None


def _uma_pergunta(client: httpx.Client, base_url: str, token: str, namespace: str, query: str) -> dict:
    t0 = time.perf_counter()
    ttft_ms = None
    with client.stream(
        "POST", f"{base_url}/api/query/stream",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": query, "namespaces": [namespace]},
        timeout=60,
    ) as resposta:
        resposta.raise_for_status()
        for linha in resposta.iter_lines():
            if not linha.startswith("data: "):
                continue
            payload = linha[len("data: "):]
            if payload == "[DONE]":
                break
            evento = json.loads(payload)
            if ttft_ms is None and evento.get("type") in ("chunk", "error", "blocked"):
                ttft_ms = (time.perf_counter() - t0) * 1000
    tempo_total_ms = (time.perf_counter() - t0) * 1000
    return {"query": query, "ttft_ms": ttft_ms, "total_ms": tempo_total_ms}


def run(base_url: str, n: int, queries: list[str]) -> dict:
    with httpx.Client() as client:
        token = _login(client, base_url)
        namespace = _descobrir_namespace_demo(client, base_url, token)
        if not namespace:
            return {
                "skipped": True,
                "motivo": "Nenhum documento indexado para o usuário demo (GET /api/ingest vazio)",
            }

        resultados = []
        for i, query in enumerate(queries[:n]):
            if i > 0:
                time.sleep(RATE_LIMIT_SLEEP_S)
            resultados.append(_uma_pergunta(client, base_url, token, namespace, query))

        return {
            "skipped": False,
            "namespace": namespace,
            "n": len(resultados),
            "rate_limit_sleep_s": RATE_LIMIT_SLEEP_S,
            "resultados": resultados,
        }
