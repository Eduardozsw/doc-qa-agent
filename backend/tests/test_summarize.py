import pytest
from unittest.mock import patch

from core.limits import get_limit


def test_summary_limits_by_plan():
    assert get_limit("free", "summaries") == 3
    assert get_limit("solo", "summaries") == 10
    assert get_limit("pro", "summaries") == 30


def test_unknown_plan_falls_back_to_free():
    assert get_limit("unknown", "summaries") == 3


@patch("agent.pdf_summarizer.retrieve")
@patch("agent.pdf_summarizer.client")
def test_generate_summary_returns_structured_data(mock_client, mock_retrieve):
    mock_retrieve.return_value = [
        (0.9, "ns1", "O relatório apresenta crescimento de 18%.", 1),
        (0.8, "ns1", "Expansão para o Sul do Brasil foi planejada.", 2),
    ]
    mock_client.chat.completions.create.return_value.choices[0].message.content = (
        '{"topicos_abordados": ["Crescimento financeiro"], "resumo": "O documento aborda..."}'
    )
    from agent.pdf_summarizer import generate_summary
    result = generate_summary("ns1")
    assert "topicos_abordados" in result
    assert "resumo" in result
    assert isinstance(result["topicos_abordados"], list)


@patch("agent.pdf_summarizer.retrieve")
def test_generate_summary_raises_when_no_chunks(mock_retrieve):
    import pytest
    mock_retrieve.return_value = []
    from agent.pdf_summarizer import generate_summary
    with pytest.raises(ValueError, match="Nenhum chunk encontrado"):
        generate_summary("ns1")


@patch("agent.pdf_summarizer.retrieve")
@patch("agent.pdf_summarizer.client")
def test_generate_summary_raises_on_invalid_structure(mock_client, mock_retrieve):
    import pytest
    mock_retrieve.return_value = [(0.9, "ns1", "texto qualquer", 1)]
    mock_client.chat.completions.create.return_value.choices[0].message.content = (
        '{"other_key": "unexpected"}'
    )
    from agent.pdf_summarizer import generate_summary
    with pytest.raises(ValueError, match="Estrutura de resposta inválida"):
        generate_summary("ns1")


# --- Service-level tests ---

@pytest.mark.asyncio
@patch("services.summarize.namespaces_db.get_namespaces")
@patch("services.summarize.namespaces_db.get_summary")
async def test_summarize_returns_cached(mock_get_summary, mock_get_namespaces):
    mock_get_namespaces.return_value = ["ns1"]
    mock_get_summary.return_value = {"topicos_abordados": ["a"], "resumo": "b"}
    from services.summarize import summarize_document
    result = await summarize_document("user1", "free", "ns1")
    assert result["cached"] is True
    assert result["resumo"] == "b"


@pytest.mark.asyncio
@patch("services.summarize.namespaces_db.get_namespaces")
async def test_summarize_raises_forbidden_when_not_owned(mock_get_namespaces):
    mock_get_namespaces.return_value = ["ns2"]
    from services.summarize import summarize_document
    from core.exceptions import ForbiddenError
    with pytest.raises(ForbiddenError):
        await summarize_document("user1", "free", "ns1")


@pytest.mark.asyncio
@patch("services.summarize.namespaces_db.get_namespaces")
@patch("services.summarize.namespaces_db.get_summary")
@patch("services.summarize.namespaces_db.count_summaries_this_month")
async def test_summarize_raises_forbidden_when_limit_reached(
    mock_count, mock_get_summary, mock_get_namespaces
):
    mock_get_namespaces.return_value = ["ns1"]
    mock_get_summary.return_value = None
    mock_count.return_value = 3  # free limit is 3
    from services.summarize import summarize_document
    from core.exceptions import ForbiddenError
    with pytest.raises(ForbiddenError, match="Limite de 3 resumos"):
        await summarize_document("user1", "free", "ns1")


@pytest.mark.asyncio
@patch("services.summarize.namespaces_db.get_namespaces")
@patch("services.summarize.namespaces_db.get_summary")
@patch("services.summarize.namespaces_db.count_summaries_this_month")
@patch("services.summarize.generate_summary")
@patch("services.summarize.namespaces_db.save_summary")
async def test_summarize_generates_and_saves(
    mock_save, mock_generate, mock_count, mock_get_summary, mock_get_namespaces
):
    mock_get_namespaces.return_value = ["ns1"]
    mock_get_summary.return_value = None
    mock_count.return_value = 1
    mock_generate.return_value = {"topicos_abordados": ["X"], "resumo": "Y"}
    from services.summarize import summarize_document
    result = await summarize_document("user1", "free", "ns1")
    mock_save.assert_called_once_with("user1", "ns1", {"topicos_abordados": ["X"], "resumo": "Y"})
    assert result["cached"] is False
    assert result["resumo"] == "Y"
