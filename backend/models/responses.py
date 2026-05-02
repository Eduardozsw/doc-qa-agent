from pydantic import BaseModel


class QueryResponse(BaseModel):
    resposta: str
    fontes: list[str]


class ListFilesResponse(BaseModel):
    arquivos: list[str]


class DeleteResponse(BaseModel):
    message: str
    arquivos: list[str]


class BillingUrlResponse(BaseModel):
    url: str


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
