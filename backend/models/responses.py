from pydantic import BaseModel


class Citacao(BaseModel):
    id: int
    documento: str
    namespace: str
    pagina: int | None = None
    trecho: str
    verificada: bool


class QueryResponse(BaseModel):
    resposta: str
    fontes: list[str]
    citacoes: list[Citacao] = []
    correcao: bool = False
    trace_id: str | None = None
    cached: bool = False


class ListFilesResponse(BaseModel):
    arquivos: list[str]


class DeleteResponse(BaseModel):
    message: str
    arquivos: list[str]


class JobInfo(BaseModel):
    job_id: str
    filename: str


class AsyncIngestResponse(BaseModel):
    jobs: list[JobInfo]
    skipped: list[str] = []


class JobStatus(BaseModel):
    status: str
    filename: str
    namespace: str | None = None
    error: str | None = None


class JobStatusResponse(BaseModel):
    jobs: dict[str, JobStatus | None]
