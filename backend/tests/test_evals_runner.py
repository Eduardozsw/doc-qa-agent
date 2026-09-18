import json
from unittest.mock import patch

from evals.runner import DATASET_PATH, EVAL_NAMESPACE, ensure_indexed, runner


@patch("evals.runner.evaluate_retrieval")
@patch("evals.runner.ensure_indexed")
@patch("evals.runner.judge")
@patch("evals.runner.orchestrator")
def test_runner_returns_metrics_dict_and_uses_eval_namespace(
    mock_orchestrator, mock_judge, mock_ensure_indexed, mock_evaluate_retrieval
):
    num_casos = len(json.loads(DATASET_PATH.read_text()))
    mock_orchestrator.return_value = {"resposta": "resposta qualquer", "fontes": []}
    mock_judge.return_value = 0.8
    mock_evaluate_retrieval.return_value = {"hit@3": 0.5, "hit@5": 0.6, "hit@8": 0.7, "mrr": 0.4}

    metricas = runner()

    mock_ensure_indexed.assert_called_once_with()
    assert mock_orchestrator.call_count == num_casos
    for call in mock_orchestrator.call_args_list:
        assert call.kwargs["namespaces"] == [EVAL_NAMESPACE]
        assert call.kwargs["plan"] == "pro"
        assert call.kwargs["use_cache"] is False

    assert metricas == {
        "answer_score": 0.8,
        "hit@3": 0.5,
        "hit@5": 0.6,
        "hit@8": 0.7,
        "mrr": 0.4,
        "citation_rate": 0.0,
        "correction_rate": 0.0,
    }


@patch("evals.runner.upsert_chunks")
@patch("evals.runner.load_pages_from_bytes")
@patch("evals.runner.vectors_db")
def test_ensure_indexed_skips_when_already_indexed(mock_vectors_db, mock_load_pages, mock_upsert_chunks):
    mock_vectors_db.count.return_value = 3

    ensure_indexed()

    mock_vectors_db.count.assert_called_once_with(EVAL_NAMESPACE)
    mock_load_pages.assert_not_called()
    mock_upsert_chunks.assert_not_called()


@patch("evals.runner.contextualize")
@patch("evals.runner.build_preview")
@patch("evals.runner.upsert_chunks")
@patch("evals.runner.load_pages_from_bytes")
@patch("evals.runner.vectors_db")
def test_ensure_indexed_indexes_pdf_into_eval_namespace(
    mock_vectors_db, mock_load_pages, mock_upsert_chunks, mock_build_preview, mock_contextualize, tmp_path
):
    mock_vectors_db.count.return_value = 0
    mock_load_pages.return_value = [(1, "texto da pagina 1")]
    mock_build_preview.return_value = "preview"
    mock_contextualize.return_value = [""]

    fake_pdf = tmp_path / "cab37_hipertensao.pdf"
    fake_pdf.write_bytes(b"%PDF-1.4 conteudo falso")

    with patch("evals.runner.DEMO_PDF_PATH", fake_pdf):
        ensure_indexed()

    mock_load_pages.assert_called_once_with(fake_pdf.read_bytes())
    mock_contextualize.assert_called_once_with([("texto da pagina 1", 1)], "preview")
    mock_upsert_chunks.assert_called_once()
    chunks_arg, doc_name_arg, namespace_arg, contexts_arg = mock_upsert_chunks.call_args[0]
    assert doc_name_arg == EVAL_NAMESPACE
    assert namespace_arg == EVAL_NAMESPACE
    assert chunks_arg == [("texto da pagina 1", 1)]
    assert contexts_arg == [""]
