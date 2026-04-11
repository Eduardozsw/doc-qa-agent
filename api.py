from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from agent.orchestrator import orchestrator
from ingestion.loader import load_document
from ingestion.chunker import chunk_text
from ingestion.embedder import upsert_chunks
from pydantic import BaseModel
import tempfile
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

@app.post("/ingest")
async def ingest(file: UploadFile):

    contents = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    lddc = load_document(tmp_path)
    chunks = chunk_text(lddc)
    upsert_chunks(chunks, file.filename or "unknown")

    os.remove(tmp_path)
    return{"message": f"{len(chunks)} chunks indexados"}
@app.post("/query")
async def query(body: QueryRequest):
    resposta = orchestrator(body.query)
    return {"resposta": resposta}