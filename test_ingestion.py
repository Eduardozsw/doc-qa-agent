from ingestion.loader import load_document
from ingestion.chunker import chunk_text
from ingestion.embedder import upsert_chunks

text = load_document("arquivo.pdf")
chunks = chunk_text(text)
upsert_chunks(chunks, "meu_doc")
print(f"{len(chunks)} chunks indexados")