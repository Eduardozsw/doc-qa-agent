from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from ingestion import contextualizer


def _fake_settings(enabled: bool = True):
    return SimpleNamespace(contextual_retrieval_enabled=enabled, openai_chat_model="gpt-4o-mini")


def _fake_response(texto: str):
    resposta = MagicMock()
    resposta.choices = [MagicMock(message=MagicMock(content=texto))]
    return resposta


@patch("ingestion.contextualizer.get_settings", return_value=_fake_settings(enabled=False))
def test_flag_desligada_devolve_vazio_sem_chamar_llm(mock_settings):
    with patch("ingestion.contextualizer._client") as mock_client:
        result = contextualizer.contextualize([("chunk um", 1), ("chunk dois", 2)], "preview")

    assert result == ["", ""]
    mock_client.assert_not_called()


@patch("ingestion.contextualizer.get_settings", return_value=_fake_settings())
@patch("ingestion.contextualizer._client")
def test_contextualize_chama_um_por_chunk_em_paralelo(mock_client, mock_settings):
    mock_client.return_value.chat.completions.create.return_value = _fake_response("Contexto qualquer.")

    chunks = [(f"chunk {i}", 1) for i in range(5)]
    result = contextualizer.contextualize(chunks, "preview do documento")

    assert result == ["Contexto qualquer."] * 5
    assert mock_client.return_value.chat.completions.create.call_count == 5


@patch("ingestion.contextualizer.get_settings", return_value=_fake_settings())
@patch("ingestion.contextualizer._client")
def test_doc_preview_vai_no_inicio_e_chunk_no_fim_do_prompt(mock_client, mock_settings):
    mock_client.return_value.chat.completions.create.return_value = _fake_response("ctx")

    contextualizer.contextualize([("meu trecho", 1)], "inicio do documento")

    _, kwargs = mock_client.return_value.chat.completions.create.call_args
    conteudo_usuario = kwargs["messages"][1]["content"]
    assert conteudo_usuario.index("inicio do documento") < conteudo_usuario.index("meu trecho")


@patch("ingestion.contextualizer.get_settings", return_value=_fake_settings())
@patch("ingestion.contextualizer._client")
def test_erro_em_um_chunk_falha_aberto_com_string_vazia(mock_client, mock_settings):
    def create_side_effect(**kwargs):
        conteudo = kwargs["messages"][1]["content"]
        if "chunk ruim" in conteudo:
            raise RuntimeError("erro da API")
        return _fake_response("ok")

    mock_client.return_value.chat.completions.create.side_effect = create_side_effect

    chunks = [("chunk bom", 1), ("chunk ruim", 1), ("outro chunk bom", 2)]
    result = contextualizer.contextualize(chunks, "preview")

    assert result == ["ok", "", "ok"]


def test_build_preview_trunca_pelos_primeiros_tokens():
    texto = " ".join(["palavra"] * 5000)
    preview = contextualizer.build_preview(texto, max_tokens=100)

    assert len(contextualizer._enc().encode(preview)) <= 100
