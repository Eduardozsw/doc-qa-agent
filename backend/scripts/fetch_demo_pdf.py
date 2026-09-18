"""Baixa o PDF de demonstração usado pelos evals (e disponível para upload manual).

Documento: Cadernos de Atenção Básica nº 37 - "Estratégias para o cuidado da
pessoa com doença crônica: Hipertensão Arterial Sistêmica" (Ministério da
Saúde, Secretaria de Atenção à Saúde, Departamento de Atenção Básica, 2013).
Publicação de domínio público (ISBN 978-85-334-2058-8).

Nota sobre a URL: o host oficial da Biblioteca Virtual em Saúde
(bvsms.saude.gov.br / bvs.saude.gov.br) resetou a conexão em todas as
tentativas feitas durante o desenvolvimento deste script (handshake TLS ok,
sem resposta HTTP - típico de bloqueio por faixa de IP de datacenter, não
reproduzido em IPs residenciais brasileiros). A URL abaixo aponta para o
mirror da Secretaria da Saúde do Estado do Tocantins, que hospeda o mesmo
arquivo oficial do Ministério da Saúde (nome do arquivo e conteúdo
conferem: "CADERNOS DE ATENÇÃO BÁSICA Nº 37 - ESTRATÉGIAS PARA CUIDADO DA
PESSOA COM DOENÇA CRÔNICA - Hipertensão arterial sistêmica.pdf", 130
páginas). Se `bvsms.saude.gov.br/bvs/publicacoes/estrategias_cuidado_pessoa_doenca_cronica.pdf`
responder 200 no seu ambiente, sinta-se livre para trocar a constante abaixo.
"""

import urllib.request
from pathlib import Path

DEMO_PDF_URL = "https://central.to.gov.br/download/106885"
DEMO_PDF_PATH = Path(__file__).parent.parent / "docs" / "examples" / "cab37_hipertensao.pdf"

_USER_AGENT = "Mozilla/5.0 (compatible; doc-qa-agent-demo-fetch/1.0)"
_TIMEOUT_SECONDS = 60


def ensure_pdf() -> Path:
    """Garante que o PDF de demonstração exista em DEMO_PDF_PATH. Idempotente."""
    if DEMO_PDF_PATH.exists() and DEMO_PDF_PATH.stat().st_size > 0:
        return DEMO_PDF_PATH

    DEMO_PDF_PATH.parent.mkdir(parents=True, exist_ok=True)

    request = urllib.request.Request(DEMO_PDF_URL, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
        content = response.read()

    if not content.startswith(b"%PDF-"):
        raise ValueError(
            f"Conteúdo baixado de {DEMO_PDF_URL} não parece ser um PDF válido "
            f"(primeiros bytes: {content[:16]!r})"
        )

    DEMO_PDF_PATH.write_bytes(content)
    return DEMO_PDF_PATH


def main() -> None:
    path = ensure_pdf()
    size_mb = path.stat().st_size / (1024 * 1024)
    print(f"PDF de demonstração disponível em {path} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    main()
