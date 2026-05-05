from unittest.mock import MagicMock, patch

from core.limits import get_limit


def test_summary_limits_by_plan():
    assert get_limit("free", "summaries") == 3
    assert get_limit("solo", "summaries") == 10
    assert get_limit("pro", "summaries") == 30


def test_unknown_plan_falls_back_to_free():
    assert get_limit("unknown", "summaries") == 3


def _mock_admin(return_data=None, count=None):
    admin = MagicMock()
    chain = admin.table.return_value.select.return_value
    chain.eq.return_value = chain
    chain.gte.return_value = chain
    chain.not_.is_.return_value = chain
    chain.single.return_value.execute.return_value.data = return_data
    chain.execute.return_value.data = return_data if return_data is not None else []
    chain.execute.return_value.count = count or 0
    admin.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock()
    return admin


@patch("db.supabase.get_admin")
def test_get_summary_returns_cached(mock_get_admin):
    mock_get_admin.return_value = _mock_admin(return_data={"summary": {"topicos_abordados": ["a"], "resumo": "b"}})
    from db.supabase import get_summary
    result = get_summary("user1", "ns1")
    assert result == {"topicos_abordados": ["a"], "resumo": "b"}


@patch("db.supabase.get_admin")
def test_get_summary_returns_none_when_not_found(mock_get_admin):
    mock_get_admin.return_value = _mock_admin(return_data=None)
    from db.supabase import get_summary
    result = get_summary("user1", "ns1")
    assert result is None


@patch("db.supabase.get_admin")
def test_count_summaries_this_month(mock_get_admin):
    mock_get_admin.return_value = _mock_admin(count=2)
    from db.supabase import count_summaries_this_month
    result = count_summaries_this_month("user1")
    assert result == 2


@patch("db.supabase.get_admin")
def test_get_namespaces_with_summaries(mock_get_admin):
    data = [{"namespace": "ns1", "filename": "doc.pdf", "summary": {"resumo": "..."}}]
    mock_get_admin.return_value = _mock_admin(return_data=data)
    from db.supabase import get_namespaces_with_summaries
    result = get_namespaces_with_summaries("user1")
    assert len(result) == 1
    assert result[0]["namespace"] == "ns1"


@patch("db.supabase.get_admin")
def test_save_summary_calls_update(mock_get_admin):
    admin = MagicMock()
    mock_get_admin.return_value = admin
    from db.supabase import save_summary
    save_summary("user1", "ns1", {"topicos_abordados": ["a"], "resumo": "b"})
    admin.table.assert_called_once_with("namespaces")
    admin.table.return_value.update.assert_called_once()


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
