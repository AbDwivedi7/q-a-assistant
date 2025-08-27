from fastapi import APIRouter, Request
from ...config import settings
router = APIRouter()

@router.get("/health")
def health(request: Request):
    return {"status":"ok","model":settings.OPENAI_MODEL}