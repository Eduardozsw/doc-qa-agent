from fastapi import APIRouter, Depends, Response

from api.deps import UserContext, get_current_user
from core.exceptions import NotFoundError
from db import documents as documents_db

router = APIRouter(prefix="/files", tags=["files"])


@router.get("/{namespace}/pdf")
async def get_pdf(namespace: str, user: UserContext = Depends(get_current_user)):
    document = documents_db.get_document(namespace, user.id)
    if document is None:
        raise NotFoundError("Documento não encontrado")

    filename, content = document
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )
