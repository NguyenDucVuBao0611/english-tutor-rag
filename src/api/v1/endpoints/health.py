"""Endpoint kiểm tra tình trạng hệ thống (Health Check)."""

from fastapi import APIRouter, Depends, status

from src.api.dependencies import get_vector_store
from src.api.schemas.common import HealthResponse
from src.core.logger import logger
from src.vector_store.chroma_store import ChromaVectorStore

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Kiểm tra trạng thái hoạt động của hệ thống",
    description="Trả về tình trạng kết nối tới ChromaDB Vector Store và thông tin phiên bản.",
)
async def check_health(
    vector_store: ChromaVectorStore = Depends(get_vector_store),
) -> HealthResponse:
    """Kiểm tra sức khỏe hệ sinh thái API và Vector DB."""
    try:
        doc_count = vector_store.count()
        chroma_status = "connected"
    except Exception as e:
        logger.error(f"[Health Check] Lỗi kết nối ChromaDB: {e}")
        doc_count = 0
        chroma_status = f"error: {str(e)}"

    return HealthResponse(
        status="healthy" if chroma_status == "connected" else "degraded",
        version="1.0.0",
        chroma_status=chroma_status,
        total_documents_in_db=doc_count,
        models={
            "llm": "gemini-3.8-flash (auto fallback gemini-3.6-flash)",
            "embedding": "text-embedding-004",
        },
    )
