from pydantic import BaseModel, field_validator, model_validator


class HistoricoItem(BaseModel):
    pergunta: str
    resposta: str

    @model_validator(mode="after")
    def validate_lengths(self):
        if not self.pergunta.strip():
            raise ValueError("pergunta não pode estar vazia")
        if not self.resposta.strip():
            raise ValueError("resposta não pode estar vazia")
        if len(self.pergunta) > 2000:
            raise ValueError("pergunta excede 2000 caracteres")
        if len(self.resposta) > 5000:
            raise ValueError("resposta excede 5000 caracteres")
        return self


class QueryRequest(BaseModel):
    query: str
    namespaces: list[str] = []

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("query não pode estar vazia")
        if len(v) > 5000:
            raise ValueError("query excede 5000 caracteres")
        return v


class FeedbackRequest(BaseModel):
    trace_id: str | None = None
    score: int
    comentario: str = ""
    pergunta: str = ""
    resposta: str = ""

    @field_validator("score")
    @classmethod
    def validate_score(cls, v: int) -> int:
        if v not in (1, -1):
            raise ValueError("score deve ser 1 ou -1")
        return v

    @field_validator("comentario")
    @classmethod
    def validate_comentario(cls, v: str) -> str:
        if len(v) > 1000:
            raise ValueError("comentario excede 1000 caracteres")
        return v


class DeleteRequest(BaseModel):
    namespaces: list[str]

    @field_validator("namespaces")
    @classmethod
    def validate_namespaces(cls, v: list) -> list:
        if not v:
            raise ValueError("namespaces não pode estar vazio")
        return v
