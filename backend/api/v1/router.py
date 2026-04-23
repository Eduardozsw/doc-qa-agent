from fastapi import APIRouter
from api.v1.endpoints import auth, ingest, query, billing

router = APIRouter(prefix="/api")
router.include_router(auth.router)
router.include_router(ingest.router)
router.include_router(query.router)
router.include_router(billing.router)
