from pathlib import Path
import fitz

def load_document(file_path: str) -> str:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

    suffix = path.suffix.lower()

    if suffix in [".txt", ".md"]:
        return path.read_text(encoding="utf-8")
    elif suffix == ".pdf":
        doc = fitz.open(str(path))
        try:
            return "\n".join(page.get_text() for page in doc)
        finally:
            doc.close()
    else:
        raise ValueError(f"Formato não suportado: {suffix}")

def load_document_from_bytes(contents: bytes) -> str:
    doc = fitz.open(stream=contents, filetype="pdf")
    try:
        return "\n".join(page.get_text() for page in doc)
    finally:
        doc.close()