import asyncio
from unittest.mock import MagicMock, patch

import openai
import pytest

from core import tracing

# --------------------------------------------------------------------------- #
# Desabilitado (sem LANGFUSE_PUBLIC_KEY/LANGFUSE_SECRET_KEY no ambiente)
# --------------------------------------------------------------------------- #

def test_disabled_by_default():
    assert tracing.tracing_enabled() is False


def test_disabled_openai_client_is_plain_openai():
    client = tracing.openai_client()
    assert type(client) is openai.OpenAI


def test_disabled_observe_is_identity():
    @tracing.observe(name="foo")
    def func(x):
        return x + 1

    assert func(1) == 2


def test_disabled_span_is_noop():
    with tracing.span("some-span", input={"a": 1}) as s:
        result = s.update(output={"b": 2})
        assert result is s

    tracing.update_trace(tags=["blocked"])


def test_disabled_root_span_active_end_span_are_noop():
    root = tracing.root_span("doc-qa-stream", input={"q": 1})
    with tracing.active(root, user_id="u1", session_id="s1"):
        pass
    tracing.end_span(root)  # não deve levantar


def test_disabled_user_session_is_noop():
    with tracing.user_session(user_id="u1", session_id="s1"):
        pass


def test_disabled_flush_is_noop():
    tracing.flush()  # não deve levantar nem tentar rede


# --------------------------------------------------------------------------- #
# Habilitado, mas com get_client()/propagate_attributes mockados (sem rede)
# --------------------------------------------------------------------------- #

def test_enabled_openai_client_uses_langfuse_wrapper(monkeypatch):
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-fake")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-fake")
    monkeypatch.setenv("LANGFUSE_BASE_URL", "http://localhost:1")

    assert tracing.tracing_enabled() is True

    client = tracing.openai_client()

    # langfuse.openai.OpenAI é a própria classe openai.OpenAI (re-exportada);
    # o tracing é feito monkey-patchando os métodos .create() das resources.
    # Importar o módulo (feito dentro de openai_client()) é o que ativa isso,
    # sem nenhuma chamada de rede.
    assert isinstance(client, openai.OpenAI)
    assert "langfuse.openai" in __import__("sys").modules
    assert hasattr(openai.resources.chat.completions.Completions.create, "__wrapped__")


def test_enabled_span_delegates_to_langfuse_client(monkeypatch):
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-fake")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-fake")
    monkeypatch.setenv("LANGFUSE_BASE_URL", "http://localhost:1")

    fake_span = MagicMock()
    fake_client = MagicMock()
    fake_client.start_as_current_observation.return_value.__enter__.return_value = fake_span
    fake_client.start_as_current_observation.return_value.__exit__.return_value = False

    with patch("langfuse.get_client", return_value=fake_client), tracing.span("doc-qa", input={"query": "oi"}) as s:
        assert s is fake_span
        s.update(output="tudo bem")

    fake_client.start_as_current_observation.assert_called_once_with(name="doc-qa", input={"query": "oi"})
    fake_span.update.assert_called_once_with(output="tudo bem")


def test_enabled_root_span_uses_start_observation(monkeypatch):
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-fake")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-fake")
    monkeypatch.setenv("LANGFUSE_BASE_URL", "http://localhost:1")

    fake_observation = MagicMock()
    fake_client = MagicMock()
    fake_client.start_observation.return_value = fake_observation

    with patch("langfuse.get_client", return_value=fake_client):
        observation = tracing.root_span("doc-qa-stream", input={"q": 1})
        tracing.end_span(observation)

    fake_client.start_observation.assert_called_once_with(name="doc-qa-stream", input={"q": 1})
    fake_observation.end.assert_called_once()


def test_enabled_active_reactivates_otel_span_without_crossing_context(monkeypatch):
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-fake")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-fake")
    monkeypatch.setenv("LANGFUSE_BASE_URL", "http://localhost:1")

    fake_observation = MagicMock()
    fake_otel_span = MagicMock()
    fake_observation._otel_span = fake_otel_span

    fake_propagate_ctx = MagicMock()
    fake_propagate_ctx.__enter__.return_value = None
    fake_propagate_ctx.__exit__.return_value = False

    with patch("opentelemetry.trace.use_span") as mock_use_span, \
            patch("langfuse.propagate_attributes", return_value=fake_propagate_ctx) as mock_propagate:
        mock_use_span.return_value.__enter__.return_value = None
        mock_use_span.return_value.__exit__.return_value = False

        with tracing.active(fake_observation, user_id="u1", session_id="s1"):
            pass

    mock_use_span.assert_called_once_with(fake_otel_span, end_on_exit=False)
    mock_propagate.assert_called_once_with(user_id="u1", session_id="s1")


def test_enabled_update_trace_delegates_to_propagate_attributes(monkeypatch):
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-fake")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-fake")
    monkeypatch.setenv("LANGFUSE_BASE_URL", "http://localhost:1")

    fake_ctx = MagicMock()
    fake_ctx.__enter__.return_value = None
    fake_ctx.__exit__.return_value = False

    with patch("langfuse.propagate_attributes", return_value=fake_ctx) as mock_propagate:
        tracing.update_trace(tags=["blocked"])

    mock_propagate.assert_called_once_with(tags=["blocked"])


def test_enabled_flush_delegates_to_langfuse_client(monkeypatch):
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-fake")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-fake")
    monkeypatch.setenv("LANGFUSE_BASE_URL", "http://localhost:1")

    fake_client = MagicMock()
    with patch("langfuse.get_client", return_value=fake_client):
        tracing.flush()

    fake_client.flush.assert_called_once()


# --------------------------------------------------------------------------- #
# Integração: orchestrator_stream servido como a API real serve (generator
# síncrono consumido via starlette.concurrency.iterate_in_threadpool, que copia
# o contexto a cada `next()` — é isso que quebra spans "current" atravessando
# yields). Usa um Langfuse real, mas com um SpanExporter EM MEMÓRIA (nenhum
# byte sai pela rede) para inspecionar os spans exportados de verdade.
# --------------------------------------------------------------------------- #

@pytest.mark.filterwarnings("ignore")
def test_stream_spans_share_trace_id_and_propagate_user_id(monkeypatch):
    from langfuse import Langfuse
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
        InMemorySpanExporter,
    )
    from starlette.concurrency import iterate_in_threadpool

    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-inmemory-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-inmemory-test")

    exporter = InMemorySpanExporter()
    # Cliente real (SDK inteiro roda de verdade), mas o exportador é em memória:
    # nada é enviado para cloud.langfuse.com nem para nenhum host de verdade.
    real_client = Langfuse(
        public_key="pk-inmemory-test",
        secret_key="sk-inmemory-test",
        span_exporter=exporter,
    )
    monkeypatch.setattr("langfuse.get_client", lambda *a, **kw: real_client)

    # Pipeline inteiro mockado: sem chamada real a OpenAI/Postgres/etc.
    monkeypatch.setattr("agent.orchestrator.rewrite_query", lambda *a, **kw: "pergunta reescrita")
    monkeypatch.setattr(
        "agent.orchestrator.search",
        lambda *a, **kw: [("id1", "doc.pdf", "trecho 1", 1), ("id2", "doc.pdf", "trecho 2", 2)],
    )
    monkeypatch.setattr("agent.orchestrator.answer_stream", lambda *a, **kw: iter(["ola ", "mundo"]))

    from guardrails.validator import Verification
    monkeypatch.setattr(
        "agent.orchestrator.verify",
        lambda *a, **kw: Verification(fundamentada=True, correcao=False, citacoes=[]),
    )

    from agent.orchestrator import orchestrator_stream

    async def consume():
        events = []
        gen = orchestrator_stream(
            "pergunta",
            namespaces=["ns"],
            plan="pro",
            user_id="user-123",
            session_id="conv-456",
        )
        async for chunk in iterate_in_threadpool(gen):
            events.append(chunk)
        return events

    events = asyncio.run(consume())

    assert any('"type": "done"' in e for e in events)
    assert sum(1 for e in events if '"type": "chunk"' in e) == 2

    real_client.flush()
    spans = exporter.get_finished_spans()
    names = {s.name for s in spans}
    assert {"doc-qa-stream", "rewrite", "retrieve", "answer", "validate"} <= names

    # Todos os spans (root + filhos) pertencem ao MESMO trace: prova de que o
    # bug de contexto perdido entre yields foi corrigido (senão answer/validate
    # apareceriam com trace_id próprio, como traces órfãos).
    trace_ids = {s.context.trace_id for s in spans}
    assert len(trace_ids) == 1

    # user_id/session_id chegaram aos filhos, não só ao span raiz.
    child_spans = [s for s in spans if s.name != "doc-qa-stream"]
    assert child_spans, "esperava pelo menos um span filho"
    for s in child_spans:
        assert s.attributes.get("user.id") == "user-123", s.name
        assert s.attributes.get("session.id") == "conv-456", s.name

    root = next(s for s in spans if s.name == "doc-qa-stream")
    assert root.attributes.get("user.id") == "user-123"
