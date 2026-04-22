def chunk_pages(pages: list[tuple[int, str]], chunk_size: int = 500, overlap: int = 50) -> list[tuple[str, int]]:
    result = []
    for page_num, text in pages:
        for chunk in chunk_text(text, chunk_size, overlap):
            result.append((chunk, page_num))
    return result


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size deve ser > 0")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap deve ser >= 0 e < chunk_size")
    if not text or not text.strip():
        return []

    palavras = text.split()
    if not palavras:
        return []

    chunks = []
    inicio = 0

    while inicio < len(palavras):
        fim = inicio + chunk_size
        chunk = " ".join(palavras[inicio:fim])
        if chunk.strip():
            chunks.append(chunk)
        inicio += chunk_size - overlap

    return chunks