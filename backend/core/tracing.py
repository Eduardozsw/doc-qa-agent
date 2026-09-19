"""Observabilidade opcional via Langfuse Cloud.

Sem LANGFUSE_PUBLIC_KEY e LANGFUSE_SECRET_KEY no ambiente, nada aqui importa nem
inicializa o SDK do langfuse: tudo vira no-op e o comportamento é idêntico a não
ter a lib instalada (ver .env.example para as variáveis aceitas).

Cuidado com generators servidos via `starlette.concurrency.iterate_in_threadpool`
(é o caso do streaming SSE em agent/orchestrator.py): cada `next()` do generator
pode rodar numa cópia NOVA do contexto (contextvars não atravessam o `yield`).
Qualquer span "current" do langfuse (attach via `start_as_current_observation`)
que fique aberto atravessando um `yield` vira órfão depois do primeiro `yield`,
e o detach no fim loga erro porque o token não bate mais. Por isso existem duas
famílias de helpers aqui:

- `span()` / `user_session()`: usam attach ("current"). Só são seguros quando o
  `with` inteiro roda numa única retomada do generator, sem `yield` no meio.
- `root_span()` + `active()` + `end_span()`: não atacham nada; servem para criar
  uma observation ANTES de um trecho com `yield` e reativá-la (via
  `opentelemetry.trace.use_span(..., end_on_exit=False)`) só nos trechos
  síncronos entre os yields.
"""
import logging
import os
from contextlib import contextmanager

import openai as _openai

import core.config  # noqa: F401 - garante que load_dotenv() já rodou antes de olhar os.environ

logger = logging.getLogger(__name__)


def tracing_enabled() -> bool:
    return bool(os.environ.get("LANGFUSE_PUBLIC_KEY")) and bool(os.environ.get("LANGFUSE_SECRET_KEY"))


# O padrão do SDK é 600 s por requisição: uma conexão que morre no meio (ex.: troca de
# rede) prenderia o usuário por 10 minutos. 30 s cobre com folga as chamadas do pipeline.
OPENAI_TIMEOUT_S = 30.0
OPENAI_MAX_RETRIES = 2


def openai_client():
    """Cliente OpenAI. Com tracing habilitado, usa o drop-in do langfuse que
    registra cada chamada (tokens, custo) como uma generation automaticamente."""
    kwargs = {"timeout": OPENAI_TIMEOUT_S, "max_retries": OPENAI_MAX_RETRIES}
    if tracing_enabled():
        from langfuse.openai import OpenAI as _LangfuseOpenAI
        return _LangfuseOpenAI(**kwargs)
    return _openai.OpenAI(**kwargs)


def observe(**kwargs):
    """Decorator @observe do langfuse, ou identidade se desabilitado."""
    if tracing_enabled():
        from langfuse import observe as _observe
        return _observe(**kwargs)
    return lambda func: func


class _NoOpSpan:
    """Substitui a observation do langfuse quando o tracing está desligado."""

    def update(self, *args, **kwargs):
        return self

    def end(self, *args, **kwargs):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


@contextmanager
def span(name: str, **kwargs):
    """Span/observation "current" do langfuse (`start_as_current_observation`).
    Só é seguro se o `with` inteiro ficar dentro de uma única retomada
    síncrona (sem `yield` no meio) — ver docstring do módulo."""
    if not tracing_enabled():
        yield _NoOpSpan()
        return

    from langfuse import get_client

    with get_client().start_as_current_observation(name=name, **kwargs) as observation:
        yield observation


def root_span(name: str, **kwargs):
    """Cria uma observation sem atachar no contexto OTel corrente (`start_observation`).
    Segura para criar antes de um trecho com `yield`. Deve ser fechada manualmente
    com `end_span()`, e reativada com `active()` para que os filhos aninhem nela."""
    if not tracing_enabled():
        return _NoOpSpan()
    from langfuse import get_client
    return get_client().start_observation(name=name, **kwargs)


def end_span(observation) -> None:
    """Fecha uma observation criada com `root_span()`. No-op se desabilitado."""
    if tracing_enabled() and observation is not None:
        observation.end()


@contextmanager
def active(observation, *, user_id: str | None = None, session_id: str | None = None):
    """Reativa `observation` (de `root_span()`) como span corrente por um único
    trecho síncrono contíguo — NUNCA deixe um `yield` dentro deste `with`.

    Também propaga user_id/session_id (via `propagate_attributes`) para os
    filhos criados dentro deste trecho: como o contexto não atravessa `yield`,
    isso precisa ser reaplicado a cada trecho reativado, não só uma vez no
    começo do trace.
    """
    if not tracing_enabled() or observation is None:
        yield
        return

    from opentelemetry import trace as otel_trace_api

    with otel_trace_api.use_span(observation._otel_span, end_on_exit=False):
        if user_id or session_id:
            from langfuse import propagate_attributes
            with propagate_attributes(
                user_id=str(user_id) if user_id else None,
                session_id=str(session_id) if session_id else None,
            ):
                yield
        else:
            yield


@contextmanager
def user_session(user_id: str | None = None, session_id: str | None = None):
    """Propaga user_id/session_id para todo span criado dentro do bloco.
    Uso simples (código 100% síncrono, sem `yield` no meio, ex.: `orchestrator`
    não-streaming). Para generators servidos via threadpool, usar `active()`."""
    if not tracing_enabled() or (not user_id and not session_id):
        yield
        return
    from langfuse import propagate_attributes
    with propagate_attributes(
        user_id=str(user_id) if user_id else None,
        session_id=str(session_id) if session_id else None,
    ):
        yield


def update_trace(*, tags: list[str] | None = None) -> None:
    """Marca tags no trace (span raiz) atualmente ativo no contexto. No-op se
    desabilitado. Precisa ser chamado com o span certo como "current" (dentro
    de `span("doc-qa", ...)` no síncrono, ou de `active(root)` no streaming)."""
    if not tracing_enabled() or not tags:
        return
    from langfuse import propagate_attributes
    with propagate_attributes(tags=tags):
        pass


def flush() -> None:
    """Envia para o Langfuse Cloud os eventos ainda em buffer. No-op se desabilitado."""
    if not tracing_enabled():
        return
    from langfuse import get_client
    get_client().flush()


def trace_id_of(observation) -> str | None:
    """Id do trace ao qual `observation` (span raiz de `span()`/`root_span()`) pertence.
    No-op (retorna None) se o tracing estiver desligado ou `observation` for None/NoOp
    (SDK 4.x do langfuse expõe `.trace_id` diretamente na observation)."""
    if not tracing_enabled() or observation is None:
        return None
    return getattr(observation, "trace_id", None)


def score(trace_id: str | None, name: str, value: int, comment: str | None = None) -> None:
    """Registra um score (ex.: feedback do usuário) no trace `trace_id` no Langfuse Cloud.
    No-op se o tracing estiver desligado ou `trace_id` for None. Qualquer exceção (rede,
    SDK) só é logada — feedback nunca deve derrubar a request."""
    if not tracing_enabled() or not trace_id:
        return
    try:
        from langfuse import get_client
        get_client().create_score(trace_id=trace_id, name=name, value=value, comment=comment)
    except Exception as e:
        logger.warning(f"tracing.score falhou: {e}")
