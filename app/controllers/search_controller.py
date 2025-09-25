from fastapi import APIRouter, Query
from app.services import search_service

router = APIRouter(prefix="/search", tags=["Search"])

@router.get("/")
def search_jobs(q: str = Query(..., description="User job search query")):
    return search_service.search_jobs(q)
