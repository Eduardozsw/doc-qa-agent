"""Instala wrappers em `chat.completions.create`/`embeddings.create` dos clientes
OpenAI reais do pipeline, só durante o benchmark, para contar tokens por modelo
sem tocar em código de produção. Cada client é uma instância normal de `OpenAI()`
(ver core/tracing.openai_client) — o wrapper substitui o método bound na própria
instância e é restaurado ao final (`uninstall`).

Clientes do pipeline de CONSULTA (contados como "custo por pergunta"):
- agent.answerer.client       (geração da resposta)
- guardrails.validator.client (verificação de citações)
- agent.reranker.client       (rerank listwise, se RERANK_ENABLED)
- agent.query_rewriter.client (expansão multi-query e reescrita com histórico)
- ingestion.embedder._client()(embedding da pergunta, via agent.retriever.retrieve)

O juiz (evals.judge.client) é instalado separado, com seu próprio tracker —
"custo de avaliação" nunca entra no custo por pergunta do produto.
"""
import threading
from dataclasses import dataclass, field


@dataclass
class CostTracker:
    """Acumulador thread-safe de tokens por modelo (chamadas rodam em ThreadPoolExecutor
    dentro de search()/retrieve())."""

    usage: dict[str, dict[str, int]] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def record(self, model: str, input_tokens: int = 0, output_tokens: int = 0) -> None:
        with self._lock:
            entrada = self.usage.setdefault(model or "unknown", {"input": 0, "output": 0})
            entrada["input"] += input_tokens
            entrada["output"] += output_tokens

    def snapshot(self) -> dict[str, dict[str, int]]:
        with self._lock:
            return {modelo: dict(valores) for modelo, valores in self.usage.items()}


def _wrap_chat_create(original, tracker: CostTracker):
    def wrapper(*args, **kwargs):
        response = original(*args, **kwargs)
        usage = getattr(response, "usage", None)
        if usage is not None:
            tracker.record(kwargs.get("model", "unknown"), usage.prompt_tokens, usage.completion_tokens)
        return response

    return wrapper


def _wrap_embeddings_create(original, tracker: CostTracker):
    def wrapper(*args, **kwargs):
        response = original(*args, **kwargs)
        usage = getattr(response, "usage", None)
        if usage is not None:
            tracker.record(kwargs.get("model", "unknown"), usage.prompt_tokens, 0)
        return response

    return wrapper


def _patch(client, tracker: CostTracker) -> tuple[object, object]:
    """Substitui `client.chat.completions.create` e `client.embeddings.create`
    (quando existirem) e devolve os originais para restauração posterior."""
    original_chat = getattr(client.chat.completions, "create", None)
    if original_chat is not None:
        client.chat.completions.create = _wrap_chat_create(original_chat, tracker)

    original_embeddings = getattr(getattr(client, "embeddings", None), "create", None)
    if original_embeddings is not None:
        client.embeddings.create = _wrap_embeddings_create(original_embeddings, tracker)

    return original_chat, original_embeddings


def _unpatch(client, originals: tuple[object, object]) -> None:
    original_chat, original_embeddings = originals
    if original_chat is not None:
        client.chat.completions.create = original_chat
    if original_embeddings is not None:
        client.embeddings.create = original_embeddings


def install_query_wrappers(tracker: CostTracker) -> callable:
    """Instala o wrapper nos clients do pipeline de consulta. Devolve `uninstall()`."""
    from agent import answerer, query_rewriter, reranker
    from guardrails import validator
    from ingestion import embedder

    alvos = [answerer.client, validator.client, reranker.client, query_rewriter.client, embedder._client()]
    originais = [(alvo, _patch(alvo, tracker)) for alvo in alvos]

    def uninstall() -> None:
        for alvo, originals in originais:
            _unpatch(alvo, originals)

    return uninstall


def install_judge_wrapper(tracker: CostTracker) -> callable:
    """Instala o wrapper no client do juiz (evals.judge), separado do tracker de consulta."""
    from evals import judge

    original = _patch(judge.client, tracker)

    def uninstall() -> None:
        _unpatch(judge.client, original)

    return uninstall
