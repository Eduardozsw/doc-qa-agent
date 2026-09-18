from unittest.mock import patch

from agent.retriever import retrieve


@patch("agent.retriever.vectors_db.query")
@patch("agent.retriever.embed_text")
def test_retrieve_merges_and_sorts_across_namespaces(mock_embed_text, mock_query):
    mock_embed_text.return_value = [0.1] * 1536

    def fake_query(namespace, embedding, top_k):
        if namespace == "ns1":
            return [(0.5, "texto ns1 baixo", 1), (0.9, "texto ns1 alto", 2)]
        if namespace == "ns2":
            return [(0.7, "texto ns2 medio", 3)]
        return []

    mock_query.side_effect = fake_query

    results = retrieve("pergunta", top_k=10, namespaces=["ns1", "ns2"])

    scores = [r[0] for r in results]
    assert scores == sorted(scores, reverse=True)
    assert results[0] == (0.9, "ns1", "texto ns1 alto", 2)
    assert len(results) == 3
    assert {r[1] for r in results} == {"ns1", "ns2"}


@patch("agent.retriever.vectors_db.query")
@patch("agent.retriever.embed_text")
def test_retrieve_empty_namespace_returns_empty(mock_embed_text, mock_query):
    mock_embed_text.return_value = [0.1] * 1536
    mock_query.return_value = []

    results = retrieve("pergunta", top_k=10, namespaces=["ns-vazio"])

    assert results == []


@patch("agent.retriever.vectors_db.query")
@patch("agent.retriever.embed_text")
def test_retrieve_passes_top_k_through(mock_embed_text, mock_query):
    mock_embed_text.return_value = [0.1] * 1536
    mock_query.return_value = []

    retrieve("pergunta", top_k=20, namespaces=["ns1"])

    mock_query.assert_called_once_with("ns1", [0.1] * 1536, 20)
