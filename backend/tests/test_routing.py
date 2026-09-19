from types import SimpleNamespace
from unittest.mock import patch


def _settings(routing_enabled: bool = True):
    return SimpleNamespace(
        model_routing_enabled=routing_enabled,
        openai_chat_model="gpt-4o-mini",
        openai_chat_model_strong="gpt-4o",
    )


def _chunk(namespace: str, texto: str = "texto"):
    return (0.9, namespace, texto, None)


@patch("agent.routing.get_settings", return_value=_settings())
def test_default_model_for_simple_single_document_question(mock_settings):
    from agent.routing import choose_model

    model = choose_model("qual o prazo de entrega?", [_chunk("u1_ab_doc.pdf")])

    assert model == "gpt-4o-mini"


@patch("agent.routing.get_settings", return_value=_settings())
def test_strong_model_when_chunks_come_from_multiple_namespaces(mock_settings):
    from agent.routing import choose_model

    chunks = [_chunk("u1_ab_doc1.pdf"), _chunk("u1_cd_doc2.pdf")]
    model = choose_model("qual o prazo?", chunks)

    assert model == "gpt-4o"


@patch("agent.routing.get_settings", return_value=_settings())
def test_strong_model_when_question_has_more_than_60_tokens(mock_settings):
    from agent.routing import choose_model

    pergunta_longa = " ".join(["palavra"] * 70)
    model = choose_model(pergunta_longa, [_chunk("u1_ab_doc.pdf")])

    assert model == "gpt-4o"


@patch("agent.routing.get_settings", return_value=_settings())
def test_strong_model_when_question_has_premise_marker(mock_settings):
    from agent.routing import choose_model

    pergunta = "Já que a meta pressórica é 140/90, qual o primeiro passo?"
    model = choose_model(pergunta, [_chunk("u1_ab_doc.pdf")])

    assert model == "gpt-4o"


@patch("agent.routing.get_settings", return_value=_settings())
def test_premise_marker_is_case_insensitive(mock_settings):
    from agent.routing import choose_model

    pergunta = "CONSIDERANDO QUE o paciente é diabético, qual a conduta?"
    model = choose_model(pergunta, [_chunk("u1_ab_doc.pdf")])

    assert model == "gpt-4o"


@patch("agent.routing.get_settings", return_value=_settings(routing_enabled=False))
def test_routing_disabled_always_returns_default_model(mock_settings):
    from agent.routing import choose_model

    chunks = [_chunk("u1_ab_doc1.pdf"), _chunk("u1_cd_doc2.pdf")]
    pergunta = "Já que a meta é 140/90, " + " ".join(["palavra"] * 70)
    model = choose_model(pergunta, chunks)

    assert model == "gpt-4o-mini"
