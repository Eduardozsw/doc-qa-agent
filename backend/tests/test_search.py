from unittest.mock import patch

from agent.search import search


def _limpar_settings():
    from core.config import get_settings
    get_settings.cache_clear()


@patch("agent.search.rerank")
@patch("agent.search.expand_query")
@patch("agent.search.retrieve")
def test_multi_query_une_e_soma_scores(mock_retrieve, mock_expand, mock_rerank):
    mock_expand.return_value = ["variante 1", "variante 2"]

    def fake_retrieve(query, top_k, namespaces, embedding=None):
        if query == "pergunta curta":
            return [(0.5, "ns", "chunk comum", 1), (0.3, "ns", "só na original", 2)]
        if query == "variante 1":
            return [(0.4, "ns", "chunk comum", 1)]
        return [(0.2, "ns", "só na variante 2", 3)]

    mock_retrieve.side_effect = fake_retrieve
    mock_rerank.return_value = None  # não deve ser chamado (poucos candidatos)

    resultados = search("pergunta curta", namespaces=["ns"], top_k=12)

    textos = {r[2]: r for r in resultados}
    assert textos["chunk comum"][0] == 0.9  # 0.5 + 0.4, somado entre a original e a variante
    assert "só na original" in textos
    assert "só na variante 2" in textos
    mock_rerank.assert_not_called()
    assert resultados[0][2] == "chunk comum"  # maior score somado vem primeiro


@patch("agent.search.expand_query")
@patch("agent.search.retrieve")
def test_pergunta_longa_nao_expande(mock_retrieve, mock_expand):
    mock_retrieve.return_value = [(0.9, "ns", "texto", 1)]
    pergunta_longa = "esta é uma pergunta com mais de oito palavras no total aqui"
    assert len(pergunta_longa.split()) >= 8

    search(pergunta_longa, namespaces=["ns"], top_k=12)

    mock_expand.assert_not_called()
    mock_retrieve.assert_called_once()


@patch("agent.search.expand_query")
@patch("agent.search.retrieve")
def test_multi_query_desligado_pula_expand(mock_retrieve, mock_expand, monkeypatch):
    monkeypatch.setenv("MULTI_QUERY_ENABLED", "false")
    _limpar_settings()
    mock_retrieve.return_value = [(0.9, "ns", "texto", 1)]

    search("pergunta curta", namespaces=["ns"], top_k=12)

    mock_expand.assert_not_called()
    _limpar_settings()


@patch("agent.search.rerank")
@patch("agent.search.expand_query")
@patch("agent.search.retrieve")
def test_rerank_reordena_candidatos(mock_retrieve, mock_expand, mock_rerank, monkeypatch):
    monkeypatch.setenv("MULTI_QUERY_ENABLED", "false")
    _limpar_settings()
    candidatos = [(1.0 - i / 100, "ns", f"texto {i}", i) for i in range(15)]
    mock_retrieve.return_value = candidatos
    reordenados = [(3, "ns", "texto 14", 14), (2, "ns", "texto 0", 0)]
    mock_rerank.return_value = reordenados

    resultados = search("pergunta", namespaces=["ns"], top_k=2)

    mock_rerank.assert_called_once_with("pergunta", candidatos, 2)
    assert resultados == reordenados
    _limpar_settings()


@patch("agent.search.rerank")
@patch("agent.search.expand_query")
@patch("agent.search.retrieve")
def test_rerank_desligado_pula_chamada(mock_retrieve, mock_expand, mock_rerank, monkeypatch):
    monkeypatch.setenv("MULTI_QUERY_ENABLED", "false")
    monkeypatch.setenv("RERANK_ENABLED", "false")
    _limpar_settings()
    candidatos = [(1.0 - i / 100, "ns", f"texto {i}", i) for i in range(15)]
    mock_retrieve.return_value = candidatos

    resultados = search("pergunta", namespaces=["ns"], top_k=5)

    mock_rerank.assert_not_called()
    assert len(resultados) == 5
    assert resultados == candidatos[:5]
    _limpar_settings()


@patch("agent.search.expand_query")
@patch("agent.search.retrieve")
def test_embedding_precomputado_e_repassado_para_retrieve(mock_retrieve, mock_expand, monkeypatch):
    """Cache semântico (F5): embedding já calculado da pergunta original chega ao
    retrieve() sem recalcular — search() nunca chama embed_text diretamente, só
    repassa o parâmetro adiante."""
    monkeypatch.setenv("MULTI_QUERY_ENABLED", "false")
    _limpar_settings()
    mock_retrieve.return_value = [(0.9, "ns", "texto", 1)]
    precomputado = [0.7] * 1536

    search("pergunta", namespaces=["ns"], top_k=12, embedding=precomputado)

    mock_retrieve.assert_called_once_with("pergunta", top_k=20, namespaces=["ns"], embedding=precomputado)
    mock_expand.assert_not_called()
    _limpar_settings()


@patch("agent.search.rerank")
@patch("agent.search.expand_query")
@patch("agent.search.retrieve")
def test_rerank_pulado_quando_poucos_candidatos(mock_retrieve, mock_expand, mock_rerank, monkeypatch):
    monkeypatch.setenv("MULTI_QUERY_ENABLED", "false")
    _limpar_settings()
    candidatos = [(0.9, "ns", "texto único", 1)]
    mock_retrieve.return_value = candidatos

    resultados = search("pergunta", namespaces=["ns"], top_k=12)

    mock_rerank.assert_not_called()
    assert resultados == candidatos
    _limpar_settings()
