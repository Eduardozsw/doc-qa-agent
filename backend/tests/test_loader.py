from pathlib import Path

import pytest

from ingestion.loader import load_pages_from_bytes

PDF_PATH = Path(__file__).parent.parent / "docs" / "examples" / "cab37_hipertensao.pdf"

pytestmark = pytest.mark.skipif(not PDF_PATH.exists(), reason="PDF de exemplo não está no repo")


@pytest.fixture(scope="module")
def paginas():
    contents = PDF_PATH.read_bytes()
    return load_pages_from_bytes(contents)


def _pagina(paginas, numero: int) -> str:
    for n, texto in paginas:
        if n == numero:
            return texto
    raise AssertionError(f"página {numero} não encontrada")


def test_tabela_3_da_pagina_35_vira_markdown_com_a_linha_do_estagio_2(paginas):
    texto = _pagina(paginas, 35)

    linhas_tabela = [linha for linha in texto.split("\n") if linha.startswith("|")]
    assert linhas_tabela, "esperava ao menos uma linha de tabela markdown na página 35"

    linha_estagio_2 = next((linha for linha in linhas_tabela if "160" in linha and "179" in linha), None)
    assert linha_estagio_2 is not None
    assert "100" in linha_estagio_2 and "109" in linha_estagio_2


def test_pagina_35_tem_cabecalho_como_linha_de_separador_markdown(paginas):
    texto = _pagina(paginas, 35)
    assert any(linha.strip() == "|---|---|---|" for linha in texto.split("\n"))


def test_titulos_viram_linhas_com_prefixo_markdown(paginas):
    texto = _pagina(paginas, 35)
    assert "## 2.4 Classificação da pressão arterial" in texto


def test_rodape_e_numero_de_pagina_removidos(paginas):
    texto = _pagina(paginas, 35)
    assert "Ministério da Saúde | Secretaria de Atenção à Saúde | Departamento de Atenção Básica" not in texto
    assert not any(linha.strip() == "34" for linha in texto.split("\n"))


def test_todas_as_paginas_sao_extraidas(paginas):
    assert len(paginas) > 100
    numeros = [n for n, _ in paginas]
    assert numeros == sorted(numeros)
