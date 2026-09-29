"""Pydantic Schemas chung cho hệ thống API."""

from typing import Dict
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Hợp đồng dữ liệu kiểm tra sức khỏe của API Server và Vector DB."""

    status: str = Field(..., description="Trạng thái hoạt động của hệ thống (healthy, degraded, error).")
    version: str = Field(..., description="Phiên bản API hiện tại.")
    chroma_status: str = Field(..., description="Trạng thái kết nối đến ChromaDB Vector Store.")
    total_documents_in_db: int = Field(..., description="Tổng số mẩu văn bản hiện có trong ChromaDB.")
    models: Dict[str, str] = Field(..., description="Thông tin các mô hình LLM và Embedding đang sử dụng.")
