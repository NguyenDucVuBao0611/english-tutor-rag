"""Endpoint tương tác hội thoại với Autonomous ReAct Tutor Agent."""

import time
from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import get_tutor_agent
from src.api.schemas.agent import (
    ChatRequest,
    ChatResponse,
    SourceMetadataResponse,
    ThoughtStepResponse,
)
from src.core.logger import logger
from src.agents.tutor_agent import TutorAgent

router = APIRouter(prefix="/agent", tags=["AI Tutor Agent"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Trò chuyện và học tiếng Anh cùng Gia Sư AI",
    description=(
        "Tiếp nhận câu hỏi hoặc câu chào từ học viên. Kích hoạt chu trình ReAct "
        "(Reasoning + Acting), tự chủ phân loại ý định (Intent Routing), "
        "tra cứu tài liệu giáo trình qua ChromaDB nếu cần và trả về lời giảng sư phạm."
    ),
)
async def chat_with_agent(
    request: ChatRequest,
    agent: TutorAgent = Depends(get_tutor_agent),
) -> ChatResponse:
    """Xử lý hội thoại thông minh cùng TutorAgent."""
    logger.info(f"[API /chat] Tiếp nhận yêu cầu: '{request.message[:80]}...' (Max iterations: {request.max_iterations})")
    start_time = time.perf_counter()

    try:
        # Gọi trực tiếp chu trình ReAct của TutorAgent
        result = agent.chat(
            user_message=request.message,
            max_iterations=request.max_iterations,
        )

        execution_time = round(time.perf_counter() - start_time, 2)
        logger.info(f"[API /chat] Xử lý thành công trong {execution_time}s.")

        # Định dạng danh sách nguồn tài liệu tham khảo
        sources = []
        for src in result.get("sources", []):
            raw_unit = src.get("unit")
            clean_unit = raw_unit if raw_unit not in ["", None, "null"] else None
            sources.append(
                SourceMetadataResponse(
                    book_title=src.get("book_title", "Unknown"),
                    page_number=src.get("page_number", 0),
                    unit=clean_unit,
                    score=round(float(src.get("score", 0.0)), 4),
                )
            )

        # Định dạng vết suy luận ReAct
        trajectory = [
            ThoughtStepResponse(
                step=step.get("step", idx + 1),
                thought=step.get("thought"),
                action=step.get("action"),
                action_input=step.get("action_input"),
                observation=step.get("observation"),
            )
            for idx, step in enumerate(result.get("thought_trajectory", []))
        ]

        return ChatResponse(
            answer=result.get("answer", ""),
            sources=sources,
            tools_used=result.get("tools_used", []),
            thought_trajectory=trajectory,
            execution_time_seconds=execution_time,
        )

    except Exception as e:
        logger.error(f"[API /chat] Lỗi khi xử lý hội thoại: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi máy chủ khi Gia Sư AI xử lý câu hỏi: {str(e)}",
        )
