from unittest.mock import MagicMock, patch

from ingestion import embedder


def _fake_openai_response(n: int):
    resp = MagicMock()
    resp.data = [MagicMock(embedding=[0.1 * i] * 1536) for i in range(n)]
    return resp


def _fake_enc():
    enc = MagicMock()
    enc.encode.side_effect = lambda t: [0] * len(t)
    return enc


def test_import_is_lazy_and_never_touched_network():
    # _client/_enc são lru_cache; se o import do módulo já os tivesse chamado
    # (como fazia o antigo `OpenAI()`/`tiktoken.encoding_for_model` no topo do
    # arquivo), o cache já estaria populado aqui.
    assert embedder._client.cache_info().currsize == 0
    assert embedder._enc.cache_info().currsize == 0


@patch("ingestion.embedder._enc")
@patch("ingestion.embedder.vectors_db.upsert_vectors")
@patch("ingestion.embedder._client")
def test_upsert_chunks_builds_ids_and_batches(mock_client, mock_upsert, mock_enc):
    mock_enc.return_value = _fake_enc()
    mock_client.return_value.embeddings.create.return_value = _fake_openai_response(3)

    chunks = [("chunk um", 1), ("chunk dois", 1), ("chunk tres", 2)]
    embedder.upsert_chunks(chunks, "doc123", "ns1")

    mock_upsert.assert_called_once()
    namespace_arg, rows = mock_upsert.call_args[0]
    assert namespace_arg == "ns1"
    assert [r[0] for r in rows] == ["doc123_chunk_0", "doc123_chunk_1", "doc123_chunk_2"]
    assert [r[1] for r in rows] == [0, 1, 2]
    assert [r[2] for r in rows] == [1, 1, 2]
    assert [r[3] for r in rows] == ["chunk um", "chunk dois", "chunk tres"]
    assert [r[4] for r in rows] == ["", "", ""]
    assert len(rows[0][5]) == 1536


@patch("ingestion.embedder._enc")
@patch("ingestion.embedder.vectors_db.upsert_vectors")
@patch("ingestion.embedder._client")
def test_upsert_chunks_embeds_context_plus_text_but_row_keeps_original_text(mock_client, mock_upsert, mock_enc):
    mock_enc.return_value = _fake_enc()
    mock_client.return_value.embeddings.create.return_value = _fake_openai_response(2)

    chunks = [("texto original um", 1), ("texto original dois", 2)]
    contexts = ["contexto do primeiro chunk", ""]
    embedder.upsert_chunks(chunks, "doc123", "ns1", contexts=contexts)

    # o embedding foi calculado sobre context + "\n\n" + text (quando há contexto)
    enviado = mock_client.return_value.embeddings.create.call_args.kwargs["input"]
    assert enviado[0] == "contexto do primeiro chunk\n\ntexto original um"
    assert enviado[1] == "texto original dois"

    # mas a linha gravada guarda o texto ORIGINAL, sem o contexto
    _, rows = mock_upsert.call_args[0]
    assert [r[3] for r in rows] == ["texto original um", "texto original dois"]
    assert [r[4] for r in rows] == ["contexto do primeiro chunk", ""]


@patch("ingestion.embedder._enc")
@patch("ingestion.embedder.vectors_db.upsert_vectors")
@patch("ingestion.embedder._client")
def test_upsert_chunks_respects_embed_batch_size(mock_client, mock_upsert, mock_enc):
    mock_enc.return_value = _fake_enc()
    total = embedder.EMBED_BATCH_SIZE + 5
    chunks = [(f"chunk {i}", 1) for i in range(total)]

    def create_side_effect(input, model):
        return _fake_openai_response(len(input))

    mock_client.return_value.embeddings.create.side_effect = create_side_effect

    embedder.upsert_chunks(chunks, "doc", "ns1")

    assert mock_client.return_value.embeddings.create.call_count == 2
    assert mock_upsert.call_count == 2


@patch("ingestion.embedder.vectors_db.delete_namespace")
def test_delete_namespace_delegates(mock_delete):
    embedder.delete_namespace("ns1")
    mock_delete.assert_called_once_with("ns1")
