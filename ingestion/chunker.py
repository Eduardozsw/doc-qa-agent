def chunk_text(text: str, chunk_size: int = 250, overlap: int = 50) -> list[str]:
    palavras = text.split()
    chunks = []
    inicio = 0

    while inicio < len(palavras):
        fim = inicio + chunk_size
        chunk = palavras[inicio:fim]
        chunks.append(" ".join(chunk))
        inicio += chunk_size - overlap

    return chunks