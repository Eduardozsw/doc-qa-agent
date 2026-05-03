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


class CheckoutRequest(BaseModel):
    plan: str
    payment_method: str = "card"

    @field_validator("plan")
    @classmethod
    def validate_plan(cls, v: str) -> str:
        if v not in ("solo", "pro"):
            raise ValueError("plano inválido")
        return v

    @field_validator("payment_method")
    @classmethod
    def validate_payment_method(cls, v: str) -> str:
        if v not in ("card", "pix"):
            raise ValueError("método de pagamento inválido")
        return v


class DeleteRequest(BaseModel):
    namespaces: list[str]

    @field_validator("namespaces")
    @classmethod
    def validate_namespaces(cls, v: list) -> list:
        if not v:
            raise ValueError("namespaces não pode estar vazio")
        return v


class DriveFileRef(BaseModel):
    file_id: str
    file_name: str

    @model_validator(mode="after")
    def validate_fields(self):
        if not self.file_id.strip():
            raise ValueError("file_id não pode estar vazio")
        if not self.file_name.strip():
            raise ValueError("file_name não pode estar vazio")
        return self


class DriveIngestRequest(BaseModel):
    files: list[DriveFileRef]
    access_token: str

    @field_validator("files")
    @classmethod
    def validate_files(cls, v: list) -> list:
        if not v:
            raise ValueError("files não pode estar vazio")
        return v

    @field_validator("access_token")
    @classmethod
    def validate_access_token(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("access_token não pode estar vazio")
        return v
