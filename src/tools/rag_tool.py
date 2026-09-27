from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.core.logger import logger
from src.services.rag_service import RAGService
from src.tools.base import BaseTool


class GrammarRetrievalInput(BaseModel):
    """Khuôn dữ liệu đầu vào cho công cụ tra cứu ngữ pháp."""
    query: str = Field(
        ...,
        description="Câu hỏi hoặc từ khóa ngữ pháp tiếng Anh cần tra cứu chính xác trong giáo trình (ví dụ: 'present perfect tense', 'passive voice').",
    )
    top_k: int = Field(
        default=3,
        description="Số lượng đoạn tài liệu giáo trình liên quan nhất cần trích xuất.",
    )


class GrammarRetrievalTool(BaseTool):
    """Công cụ Agentic RAG: Tra cứu kiến thức ngữ pháp từ kho sách giáo trình trong ChromaDB."""

    name: str = "search_grammar_knowledge"
    description: str = (
        "Sử dụng công cụ này khi học viên hỏi về các quy tắc ngữ pháp, cấu trúc câu, từ vựng, "
        "hoặc khi cần kiểm chứng lý thuyết tiếng Anh từ giáo trình chính thống. "
        "Công cụ sẽ tìm kiếm trong Vector Database và trả về các đoạn trích từ sách kèm số trang."
    )
    args_schema: type[BaseModel] = GrammarRetrievalInput

    def __init__(self, rag_service: Optional[RAGService] = None) -> None:
        """Khởi tạo công cụ với một RAGService instance."""
        self.rag_service = rag_service or RAGService()
        self.last_retrieved_sources: List[Dict[str, Any]] = []

    def execute(self, query: str, top_k: int = 3, **kwargs: Any) -> str:
        """Thực thi việc tra cứu và định dạng văn bản cho Agent quan sát."""
        logger.info(f"[Tool: {self.name}] Đang tra cứu giáo trình cho query: '{query}' (top_k={top_k})")
        
        chunks = self.rag_service.retrieve_context(question=query, top_k=top_k)
        self.last_retrieved_sources = []

        if not chunks:
            return "Không tìm thấy tài liệu nào liên quan trong kho giáo trình tiếng Anh."

        formatted_outputs: List[str] = []
        for idx, chunk in enumerate(chunks, 1):
            meta = chunk.get("metadata", {})
            book = meta.get("book_title", "Giáo trình")
            page = meta.get("page_number", "?")
            unit = meta.get("unit", "")
            unit_str = f", Unit {unit}" if unit else ""
            content = chunk.get("document", "").strip()

            self.last_retrieved_sources.append(
                {
                    "book_title": book,
                    "page_number": page,
                    "unit": unit,
                    "score": chunk.get("score", 0.0),
                }
            )

            formatted_outputs.append(
                f"[Trích đoạn {idx} | Sách: {book}{unit_str} - Trang {page}]\n{content}"
            )

        result_text = "\n\n".join(formatted_outputs)
        logger.info(f"[Tool: {self.name}] Đã tìm thấy {len(chunks)} đoạn trích từ giáo trình.")
        return result_text
