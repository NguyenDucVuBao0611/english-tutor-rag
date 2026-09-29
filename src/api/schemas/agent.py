"""Pydantic Schemas cho Agent Chat API."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Hợp đồng dữ liệu yêu cầu trò chuyện từ học viên."""

    message: str = Field(
        ...,
        min_length=1,
        description="Nội dung câu hỏi hoặc câu chào của học viên.",
        examples=["Thầy ơi giải thích giúp em câu Bị động (Passive Voice) và cho ví dụ trong sách nhé!"],
    )
    max_iterations: int = Field(
        default=4,
        ge=1,
        le=10,
        description="Số vòng lặp suy luận ReAct tối đa của Agent.",
        examples=[4],
    )


class SourceMetadataResponse(BaseModel):
    """Hợp đồng dữ liệu trích dẫn nguồn sách giáo trình."""

    book_title: str = Field(..., description="Tên sách giáo trình được tham chiếu.")
    page_number: int = Field(..., description="Số trang trong sách giáo trình.")
    unit: Optional[Any] = Field(default=None, description="Bài học (Unit).")
    score: float = Field(default=0.0, description="Độ tương đồng ngữ nghĩa Cosine Similarity.")


class ThoughtStepResponse(BaseModel):
    """Chi tiết từng bước suy luận trong vết tư duy (Thought Trajectory) của Agent."""

    step: int = Field(..., description="Thứ tự bước lặp suy luận.")
    thought: Optional[str] = Field(default=None, description="Suy nghĩ nội tâm của Agent.")
    action: Optional[str] = Field(default=None, description="Tên công cụ Agent kích hoạt.")
    action_input: Optional[Any] = Field(default=None, description="Tham số truyền vào công cụ.")
    observation: Optional[str] = Field(default=None, description="Kết quả quan sát nhận được từ công cụ.")


class ChatResponse(BaseModel):
    """Hợp đồng dữ liệu phản hồi hoàn chỉnh từ Gia Sư AI."""

    answer: str = Field(..., description="Lời giảng sư phạm chi tiết và chuẩn xác của Agent.")
    sources: List[SourceMetadataResponse] = Field(
        default_factory=list,
        description="Danh sách các đoạn sách chính thống đã được trích dẫn.",
    )
    tools_used: List[str] = Field(
        default_factory=list,
        description="Danh sách các công cụ mà Agent đã kích hoạt trong chu trình ReAct.",
    )
    thought_trajectory: List[ThoughtStepResponse] = Field(
        default_factory=list,
        description="Toàn bộ nhật ký suy luận ReAct để kiểm tra tính minh bạch và gỡ lỗi.",
    )
    execution_time_seconds: Optional[float] = Field(
        default=None,
        description="Thời gian Agent thực thi và phản hồi tính bằng giây.",
    )
