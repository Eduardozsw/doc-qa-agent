import json
from unittest.mock import patch

import pytest

from check_regression import comparar, formatar_tabela, main


def test_comparar_detecta_regressao_alem_da_tolerancia():
    baseline = {"answer_score": 0.75, "hit@5": 0.6}
    atual = {"answer_score": 0.75, "hit@5": 0.5}  # caiu 0.1, além da tolerância de 0.07

    linhas = comparar(baseline, atual)

    regressoes = {metrica: regrediu for metrica, _, _, regrediu in linhas}
    assert regressoes == {"answer_score": False, "hit@5": True}


def test_comparar_dentro_da_tolerancia_nao_regride():
    baseline = {"answer_score": 0.75}
    atual = {"answer_score": 0.69}  # caiu 0.06: regrediria com tolerância de 0.05, mas não com 0.07

    linhas = comparar(baseline, atual)

    assert linhas[0][3] is False


def test_formatar_tabela_marca_status_por_metrica():
    linhas = [("answer_score", 0.75, 0.5, True), ("hit@5", 0.6, 0.6, False)]

    tabela = formatar_tabela(linhas)

    assert "FALHOU" in tabela
    assert "OK" in tabela
    assert "answer_score" in tabela
    assert "hit@5" in tabela


@patch("check_regression.runner")
@patch("check_regression.init_db")
def test_main_falha_com_regressao_e_grava_last_run(mock_init_db, mock_runner, tmp_path):
    mock_runner.return_value = {"answer_score": 0.5}

    baseline_path = tmp_path / "main.json"
    baseline_path.write_text(json.dumps({"answer_score": 0.75}))
    last_run_path = tmp_path / "last_run.json"

    with (
        patch("check_regression.BASELINE_PATH", baseline_path),
        patch("check_regression.LAST_RUN_PATH", last_run_path),
        pytest.raises(SystemExit),
    ):
        main()

    assert json.loads(last_run_path.read_text()) == {"answer_score": 0.5}


@patch("check_regression.runner")
@patch("check_regression.init_db")
def test_main_passa_dentro_da_tolerancia_sem_sair(mock_init_db, mock_runner, tmp_path):
    mock_runner.return_value = {"answer_score": 0.74}

    baseline_path = tmp_path / "main.json"
    baseline_path.write_text(json.dumps({"answer_score": 0.75}))
    last_run_path = tmp_path / "last_run.json"

    with (
        patch("check_regression.BASELINE_PATH", baseline_path),
        patch("check_regression.LAST_RUN_PATH", last_run_path),
    ):
        main()  # não deve levantar SystemExit


@patch("check_regression.runner")
@patch("check_regression.init_db")
def test_main_escreve_resumo_no_github_step_summary(mock_init_db, mock_runner, tmp_path, monkeypatch):
    mock_runner.return_value = {"answer_score": 0.8}

    baseline_path = tmp_path / "main.json"
    baseline_path.write_text(json.dumps({"answer_score": 0.75}))
    last_run_path = tmp_path / "last_run.json"
    summary_path = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_path))

    with (
        patch("check_regression.BASELINE_PATH", baseline_path),
        patch("check_regression.LAST_RUN_PATH", last_run_path),
    ):
        main()

    assert "answer_score" in summary_path.read_text()
