from pathlib import Path
from pypdf import PdfReader

def load_document(file_path: str) -> str:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
    
    suffix = path.suffix.lower()

    if suffix in [".txt", ".md"]:
        return path.read_text(encoding="utf-8")
    elif suffix == ".pdf":
        reader = PdfReader(str(path))
        text = []

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)

        return "\n".join(text)
    
    else:
        raise ValueError(f"Formato não suportado: {suffix}")