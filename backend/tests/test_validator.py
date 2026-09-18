import json
from unittest.mock import MagicMock, patch


def _chunk(texto: str, namespace: str = "u1_ab_doc.pdf", pagina=None, score: float = 0.9):
    return (score, namespace, texto, pagina)


def _response(content: str):
    choice = MagicMock()
    choice.message.content = content
    response = MagicMock()
    response.choices = [choice]
    response.usage = MagicMock(prompt_tokens=10, completion_tokens=5)
    return response


def _valid_payload(fundamentada=True, correcao=False, citacoes=None):
    return json.dumps({
        "fundamentada": fundamentada,
        "correcao": correcao,
        "citacoes": citacoes or [],
    })


@patch("guardrails.validator.time.sleep")
@patch("guardrails.validator.client")
def test_verify_success_marks_matching_citation_as_verificada(mock_client, mock_sleep):
    from guardrails.validator import verify
    chunks = [_chunk("O prazo é 30 dias, conforme a cláusula 3.")]
    payload = _valid_payload(citacoes=[{"id": 1, "trecho": "O prazo é 30 dias, conforme a cláusula 3."}])
    mock_client.chat.completions.create.return_value = _response(payload)

    result = verify("qual o prazo?", chunks, "o prazo é 30 dias [1]")

    assert result.fundamentada is True
    assert result.correcao is False
    assert len(result.citacoes) == 1
    assert result.citacoes[0].id == 1
    assert result.citacoes[0].verificada is True
    mock_sleep.assert_not_called()


@patch("guardrails.validator.time.sleep")
@patch("guardrails.validator.client")
def test_verify_nonexistent_citation_marks_unverified(mock_client, mock_sleep):
    from guardrails.validator import verify
    chunks = [_chunk("O prazo é 30 dias, conforme a cláusula 3.")]
    payload = _valid_payload(citacoes=[{"id": 1, "trecho": "O prazo é de 60 dias."}])
    mock_client.chat.completions.create.return_value = _response(payload)

    result = verify("qual o prazo?", chunks, "o prazo é 60 dias [1]")

    assert result.citacoes[0].verificada is False
    assert result.citacoes[0].trecho  # fallback preencheu com alguma sentença do chunk


@patch("guardrails.validator.time.sleep")
@patch("guardrails.validator.client")
def test_verify_invalid_json_three_times_fails_closed_and_calls_on_retry(mock_client, mock_sleep):
    from guardrails.validator import verify
    mock_client.chat.completions.create.return_value = _response("isso não é json")
    on_retry = MagicMock()

    result = verify("pergunta", [_chunk("chunk")], "resposta [1]", on_retry=on_retry)

    assert result.fundamentada is False
    assert result.citacoes == []
    assert on_retry.call_count == 2
    on_retry.assert_any_call(2)
    on_retry.assert_any_call(3)
    assert mock_sleep.call_count == 2
    mock_sleep.assert_any_call(0.5)
    mock_sleep.assert_any_call(1.5)


@patch("guardrails.validator.time.sleep")
@patch("guardrails.validator.client")
def test_verify_fails_once_then_succeeds(mock_client, mock_sleep):
    from guardrails.validator import verify
    payload = _valid_payload(citacoes=[{"id": 1, "trecho": "chunk"}])
    mock_client.chat.completions.create.side_effect = [Exception("falha transitória"), _response(payload)]
    on_retry = MagicMock()

    result = verify("pergunta", [_chunk("chunk")], "resposta [1]", on_retry=on_retry)

    assert result.fundamentada is True
    on_retry.assert_called_once_with(2)
    mock_sleep.assert_called_once_with(0.5)


@patch("guardrails.validator.time.sleep")
@patch("guardrails.validator.client")
def test_verify_sem_info_does_not_call_llm(mock_client, mock_sleep):
    from agent.context import _SEM_INFO
    from guardrails.validator import verify

    result = verify("pergunta", [_chunk("chunk")], _SEM_INFO)

    assert result.fundamentada is True
    assert result.citacoes == []
    mock_client.chat.completions.create.assert_not_called()
    mock_sleep.assert_not_called()


@patch("guardrails.validator.time.sleep")
@patch("guardrails.validator.client")
def test_verify_citacao_com_hifen_de_quebra_e_verificada(mock_client, mock_sleep):
    from guardrails.validator import verify
    chunks = [_chunk("O tratamento é aplicado relati- vamente rápido, conforme o protocolo.")]
    payload = _valid_payload(
        citacoes=[{"id": 1, "trecho": "O tratamento é aplicado relativamente rápido, conforme o protocolo."}]
    )
    mock_client.chat.completions.create.return_value = _response(payload)

    result = verify("qual a velocidade?", chunks, "o tratamento é relativamente rápido [1]")

    assert result.citacoes[0].verificada is True


@patch("guardrails.validator.time.sleep")
@patch("guardrails.validator.client")
def test_verify_citacao_com_diferenca_de_maiusculas_mmhg_e_verificada(mock_client, mock_sleep):
    from guardrails.validator import verify
    chunks = [_chunk("A pressão sistólica de 140 mmHG é considerada elevada.")]
    payload = _valid_payload(citacoes=[{"id": 1, "trecho": "A pressão sistólica de 140 mmHg é considerada elevada."}])
    mock_client.chat.completions.create.return_value = _response(payload)

    result = verify("qual a pressão?", chunks, "a pressão sistólica é 140 mmHg [1]")

    assert result.citacoes[0].verificada is True


@patch("guardrails.validator.time.sleep")
@patch("guardrails.validator.client")
def test_verify_citacao_com_bullet_x07_e_verificada(mock_client, mock_sleep):
    from guardrails.validator import verify
    chunks = [_chunk("\x07 O paciente deve tomar 2 comprimidos ao dia.")]
    payload = _valid_payload(citacoes=[{"id": 1, "trecho": "O paciente deve tomar 2 comprimidos ao dia."}])
    mock_client.chat.completions.create.return_value = _response(payload)

    result = verify("qual a dose?", chunks, "o paciente deve tomar 2 comprimidos ao dia [1]")

    assert result.citacoes[0].verificada is True


_CHUNK_CONTRATO = (
    "O contrato estabelece que o pagamento deve ser realizado em até trinta dias corridos "
    "após a emissão da nota fiscal, salvo disposição em contrário."
)


@patch("guardrails.validator.time.sleep")
@patch("guardrails.validator.client")
def test_verify_citacao_com_cauda_divergente_mas_4grams_acima_de_08_e_verificada(mock_client, mock_sleep):
    from guardrails.validator import verify
    chunks = [_chunk(_CHUNK_CONTRATO)]
    # mesmas 20 primeiras palavras do chunk; últimas 4 palavras parafraseadas
    trecho = (
        "O contrato estabelece que o pagamento deve ser realizado em até trinta dias corridos "
        "após a emissão da nota fiscal exceto quando acordado diferente"
    )
    payload = _valid_payload(citacoes=[{"id": 1, "trecho": trecho}])
    mock_client.chat.completions.create.return_value = _response(payload)

    result = verify("qual o prazo de pagamento?", chunks, "o pagamento deve ser em até 30 dias [1]")

    assert result.citacoes[0].verificada is True
    assert result.citacoes[0].trecho == trecho  # mantém o trecho do LLM, sem cair no fallback


@patch("guardrails.validator.time.sleep")
@patch("guardrails.validator.client")
def test_verify_citacao_com_cauda_muito_divergente_abaixo_de_08_nao_e_verificada(mock_client, mock_sleep):
    from guardrails.validator import verify
    chunks = [_chunk(_CHUNK_CONTRATO)]
    # só as 10 primeiras palavras batem com o chunk; o resto é parafraseado/inventado
    trecho = (
        "O contrato estabelece que o pagamento deve ser realizado imediatamente "
        "sem qualquer prazo adicional e sem possibilidade de prorrogação por nenhuma das partes envolvidas"
    )
    payload = _valid_payload(citacoes=[{"id": 1, "trecho": trecho}])
    mock_client.chat.completions.create.return_value = _response(payload)

    result = verify("qual o prazo de pagamento?", chunks, "o pagamento é imediato [1]")

    assert result.citacoes[0].verificada is False
    assert result.citacoes[0].trecho  # fallback preencheu com alguma sentença do chunk


@patch("guardrails.validator.time.sleep")
@patch("guardrails.validator.client")
def test_verify_citacao_curta_sem_containment_nao_e_verificada(mock_client, mock_sleep):
    from guardrails.validator import verify
    chunks = [_chunk(_CHUNK_CONTRATO)]
    payload = _valid_payload(citacoes=[{"id": 1, "trecho": "prazo sessenta dias"}])
    mock_client.chat.completions.create.return_value = _response(payload)

    result = verify("qual o prazo?", chunks, "o prazo é sessenta dias [1]")

    assert result.citacoes[0].verificada is False
