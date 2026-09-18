from unittest.mock import patch

from agent.retriever import retrieve


@patch("agent.retriever.vectors_db.query_keyword")
@patch("agent.retriever.vectors_db.query")
@patch("agent.retriever.embed_text")
def test_rrf_merges_and_dedupes_hits_from_both_sources(mock_embed_text, mock_query, mock_query_keyword):
    mock_embed_text.return_value = [0.1] * 1536
    # mesmo chunk (namespace, texto) aparece nas duas buscas -> deve fundir, não duplicar
    mock_query.return_value = [(0.9, "chunk comum", 1), (0.5, "só no vetorial", 2)]
    mock_query_keyword.return_value = [(0.8, "chunk comum", 1), (0.7, "só no keyword", 3)]

    results = retrieve("pergunta", top_k=10, namespaces=["ns1"])

    textos = [r[2] for r in results]
    assert textos.count("chunk comum") == 1
    assert "só no vetorial" in textos
    assert "só no keyword" in textos
    # chunk comum aparece nas duas listas em 1º lugar -> maior score RRF, vem primeiro
    assert results[0][2] == "chunk comum"


@patch("agent.retriever.vectors_db.query_keyword")
@patch("agent.retriever.vectors_db.query")
@patch("agent.retriever.embed_text")
def test_item_only_in_keyword_search_is_included(mock_embed_text, mock_query, mock_query_keyword):
    mock_embed_text.return_value = [0.1] * 1536
    mock_query.return_value = []
    mock_query_keyword.return_value = [(0.6, "achado só por palavra-chave", 5)]

    results = retrieve("pergunta", top_k=10, namespaces=["ns1"])

    assert len(results) == 1
    assert results[0][2] == "achado só por palavra-chave"
    assert results[0][3] == 5


@patch("agent.retriever.vectors_db.query_keyword")
@patch("agent.retriever.vectors_db.query")
@patch("agent.retriever.embed_text")
def test_hybrid_search_false_ignores_keyword(mock_embed_text, mock_query, mock_query_keyword, monkeypatch):
    from core.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("HYBRID_SEARCH", "false")
    mock_embed_text.return_value = [0.1] * 1536
    mock_query.return_value = [(0.9, "texto vetorial", 1)]

    results = retrieve("pergunta", top_k=10, namespaces=["ns1"])

    mock_query_keyword.assert_not_called()
    assert len(results) == 1
    assert results[0][2] == "texto vetorial"

    get_settings.cache_clear()


@patch("agent.retriever.vectors_db.query_keyword")
@patch("agent.retriever.vectors_db.query")
@patch("agent.retriever.embed_text")
def test_retrieve_cuts_at_top_k(mock_embed_text, mock_query, mock_query_keyword):
    mock_embed_text.return_value = [0.1] * 1536
    mock_query.return_value = [(1.0 - i / 100, f"texto {i}", i) for i in range(20)]
    mock_query_keyword.return_value = []

    results = retrieve("pergunta", top_k=5, namespaces=["ns1"])

    assert len(results) == 5


@patch("agent.retriever.vectors_db.query_keyword")
@patch("agent.retriever.vectors_db.query")
@patch("agent.retriever.embed_text")
def test_retrieve_empty_namespace_returns_empty(mock_embed_text, mock_query, mock_query_keyword):
    mock_embed_text.return_value = [0.1] * 1536
    mock_query.return_value = []
    mock_query_keyword.return_value = []

    results = retrieve("pergunta", top_k=10, namespaces=["ns-vazio"])

    assert results == []


@patch("agent.retriever.vectors_db.query_keyword")
@patch("agent.retriever.vectors_db.query")
@patch("agent.retriever.embed_text")
def test_embedding_computed_once_regardless_of_namespaces(mock_embed_text, mock_query, mock_query_keyword):
    mock_embed_text.return_value = [0.1] * 1536
    mock_query.return_value = []
    mock_query_keyword.return_value = []

    retrieve("pergunta", top_k=10, namespaces=["ns1", "ns2", "ns3"])

    mock_embed_text.assert_called_once_with("pergunta")
