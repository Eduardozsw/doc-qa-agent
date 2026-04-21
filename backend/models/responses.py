from pydantic import BaseModel


class IngestResponse(BaseModel):
    message: str
    arquivos: list[str]


class QueryResponse(BaseModel):
    resposta: str
    fontes: list[str]


class ListFilesResponse(BaseModel):
    arquivos: list[str]


class DeleteResponse(BaseModel):
    message: str
    arquivos: list[str]
