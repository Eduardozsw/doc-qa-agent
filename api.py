from fastapi import FastAPI, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from agent.orchestrator import orchestrator
from ingestion.loader import load_document
from ingestion.chunker import chunk_text
from ingestion.embedder import upsert_chunks, delete_namespace
from storage.redis_client import get_namespaces, add_namespace, remove_namespace
from auth.middleware import get_current_user
from pydantic import BaseModel
from typing import List
import tempfile
import unicodedata
import re
import os

def sanitize_namespace(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^A-Za-z0-9._\-]", "_", ascii_name)

app = FastAPI()

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str
    namespaces: list[str] = [""]
    historico: list[dict] = []

class DeleteRequest(BaseModel):
    namespaces: list[str]

@app.get("/ingest")
async def list_ingest(_: dict = Depends(get_current_user)):
    return {"arquivos": get_namespaces()}

@app.delete("/ingest", status_code=200)
async def remove_ingest(body: DeleteRequest, _: dict = Depends(get_current_user)):
    namespaces = get_namespaces()

    not_found = [n for n in body.namespaces if n not in namespaces]
    if not_found:
        raise HTTPException(status_code=404, detail=f"Arquivos não encontrados: {not_found}")

    for namespace in body.namespaces:
        delete_namespace(namespace)
        remove_namespace(namespace)

    return {"message": f"{len(body.namespaces)} arquivo(s) removido(s)", "arquivos": body.namespaces}

@app.post("/ingest", status_code=200)
async def ingest(files: List[UploadFile], _: dict = Depends(get_current_user)):
    namespaces = get_namespaces()
    slots_available = 5 - len(namespaces)

    if slots_available <= 0:
        raise HTTPException(status_code=400, detail="Limite de 5 documentos atingido")

    if len(files) > slots_available:
        raise HTTPException(
            status_code=400,
            detail=f"Você pode adicionar no máximo {slots_available} arquivo(s) mais"
        )   

    for file in files:
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=415, detail=f"Arquivo '{file.filename}' não é um PDF")

    total_chunks = 0
    added = []

    for file in files:
        contents = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        lddc = load_document(tmp_path)
        print(f"Texto extraído: {len(lddc)} caracteres")
        chunks = chunk_text(lddc)
        print(f"Chunks gerados: {len(chunks)}")
        namespace = sanitize_namespace(file.filename or "unknown")
        upsert_chunks(chunks, namespace, namespace=namespace)
        os.remove(tmp_path)

        add_namespace(namespace)
        added.append(namespace)
        total_chunks += len(chunks)

    return {"message": f"{total_chunks} chunks indexados", "arquivos": added}

@app.post("/query")
async def query(body: QueryRequest, _: dict = Depends(get_current_user)):
    namespaces = body.namespaces if body.namespaces != [""] else get_namespaces()
    result = orchestrator(body.query, namespaces=namespaces, historico=body.historico)
    return result
