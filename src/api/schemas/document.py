"""Pydantic Schemas cho Document Management API."""

from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    """Hợp đồng dữ liệu trả về sau khi tải lên và nạp tài liệu vào kho Vector DB."""

    filename: str = Field(..., description="Tên tệp tin đã tải lên.")
    file_type: str = Field(..., description="Định dạng tệp tin (pdf, txt).")
    total_pages: int = Field(..., description="Tổng số trang văn bản đã đọc được.")
    total_chunks: int = Field(..., description="Số đoạn phân đoạn (Chunks) đã chia và tạo vector.")
    message: str = Field(..., description="Thông báo kết quả xử lý từ hệ thống.")
    status: str = Field(default="success", description="Trạng thái xử lý (success / error).")
