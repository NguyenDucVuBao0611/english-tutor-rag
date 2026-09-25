from typing import Any, Dict, List, Optional

from src.core.logger import logger
from src.services.llm_service import LLMService
from src.vector_store.base import BaseVectorStore
from src.vector_store.chroma_store import ChromaVectorStore

# System Prompt mẫu chuẩn Enterprise cho Gia sư Tiếng Anh (Grounded Prompting)
DEFAULT_TUTOR_SYSTEM_INSTRUCTION = """Bạn là một Gia Sư Tiếng Anh (AI English Tutor) chuyên nghiệp, kiên nhẫn và tận tâm.
Nhiệm vụ của bạn là giải thích các chủ điểm ngữ pháp, cấu trúc câu, từ vựng và bài tập tiếng Anh cho học viên Việt Nam.

QUY TẮC KỶ LUẬT THÉP (GROUNDING RULES):
1. CHÂN LÝ TỪ NGỮ CẢNH: Mọi lời giải thích, cấu trúc ngữ pháp và ví dụ bạn đưa ra BẮT BUỘC phải dựa trên thông tin nằm trong thẻ <context>...</context> được cung cấp.
2. NGUYÊN TẮC TỪ CHỐI AN TOÀN (REFUSAL POLICY): Nếu câu hỏi của học viên hoàn toàn KHÔNG LIÊN QUAN hoặc KHÔNG CÓ THÔNG TIN trong tài liệu <context>, bạn BẮT BUỘC phải trả lời chính xác:
   "Xin lỗi bạn, tài liệu giáo trình tiếng Anh hiện tại chưa có thông tin về nội dung này. Bạn vui lòng kiểm tra lại hoặc hỏi về các chủ đề ngữ pháp trong sách nhé!"
   Tuyệt đối KHÔNG tự ý suy diễn hoặc dùng kiến thức ngoài đời để bịa đặt câu trả lời.
3. BẮT BUỘC TRÍCH DẪN NGUỒN (SOURCE CITATION): Cuối câu trả lời, hãy luôn liệt kê rõ nguồn gốc tài liệu đã tham khảo theo định dạng:
   📚 **Nguồn tham khảo**: [Tên sách - Trang X]
4. PHONG CÁCH SƯ PHẠM: Giải thích bản chất ngữ pháp bằng tiếng Việt tự nhiên, gãy gọn. Các ví dụ minh họa và cấu trúc câu luôn trình bày bằng tiếng Anh chuẩn mực, rõ ràng."""


class RAGService:
    """Facade Service điều phối toàn bộ quy trình RAG (Retrieval-Augmented Generation).
    
    Áp dụng Facade Pattern để che giấu sự phức tạp của việc phối hợp giữa
    Vector Database (ChromaDB), Embedding Service, Grounded Prompting và LLM Service.
    """

    def __init__(
        self,
        vector_store: Optional[BaseVectorStore] = None,
        llm_service: Optional[LLMService] = None,
        system_instruction: str = DEFAULT_TUTOR_SYSTEM_INSTRUCTION,
    ) -> None:
        """Khởi tạo RAGService với các dependencies có thể inject linh hoạt.

        Args:
            vector_store (Optional[BaseVectorStore]): Kho lưu trữ vector (mặc định là ChromaVectorStore).
            llm_service (Optional[LLMService]): Dịch vụ sinh văn bản LLM (mặc định là LLMService Singleton).
            system_instruction (str): Chỉ thị hệ thống neo ngữ cảnh chống ảo giác.
        """
        self.vector_store = vector_store or ChromaVectorStore()
        self.llm_service = llm_service or LLMService()
        self.system_instruction = system_instruction
        logger.info("Khởi tạo thành công RAGService Facade.")

    def retrieve_context(
        self,
        question: str,
        top_k: int = 3,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Truy vấn Top-k đoạn văn bản liên quan nhất từ Vector Database.
        
        Phương thức này đóng vai trò độc lập, sẵn sàng để đóng gói thành Agent Tool ở Ngày 7.

        Args:
            question (str): Câu hỏi của người học.
            top_k (int): Số lượng đoạn trích liên quan nhất cần lấy.
            where (Optional[Dict[str, Any]]): Bộ lọc metadata (vd: theo sách, trang).

        Returns:
            List[Dict[str, Any]]: Danh sách các chunks kèm metadata và điểm tương đồng.
        """
        logger.info(f"RAGService đang truy xuất ngữ cảnh cho câu hỏi: '{question[:50]}...'")
        return self.vector_store.similarity_search(query=question, top_k=top_k, where=where)

    def build_grounded_prompt(
        self,
        question: str,
        context_chunks: List[Dict[str, Any]],
    ) -> str:
        """Ghép nối câu hỏi của học viên và các đoạn trích từ sách thành Grounded Prompt.

        Args:
            question (str): Câu hỏi gốc.
            context_chunks (List[Dict[str, Any]]): Danh sách các chunks trích từ ChromaDB.

        Returns:
            str: Prompt hoàn chỉnh đóng khung trong thẻ <context>.
        """
        if not context_chunks:
            formatted_context = "KHÔNG TÌM THẤY TÀI LIỆU NÀO PHÙ HỢP TRONG GIÁO TRÌNH."
        else:
            context_parts: List[str] = []
            for idx, chunk in enumerate(context_chunks, 1):
                meta = chunk.get("metadata", {})
                book = meta.get("book_title", "Giáo trình Tiếng Anh")
                page = meta.get("page_number", "?")
                unit = meta.get("unit", "")
                unit_str = f", Unit {unit}" if unit else ""
                
                header = f"[Tài liệu {idx} - Sách: {book}{unit_str}, Trang: {page}]"
                content = chunk.get("document", "").strip()
                context_parts.append(f"{header}\n{content}")

            formatted_context = "\n\n".join(context_parts)

        grounded_prompt = (
            f"<context>\n"
            f"{formatted_context}\n"
            f"</context>\n\n"
            f"Câu hỏi của học viên: {question}\n\n"
            f"Hãy trả lời câu hỏi trên theo đúng các quy tắc kỷ luật đã nêu."
        )
        return grounded_prompt

    def ask(
        self,
        question: str,
        top_k: int = 3,
        where: Optional[Dict[str, Any]] = None,
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        """Phương thức Facade chính: Tiếp nhận câu hỏi và trả về câu trả lời hoàn chỉnh kèm nguồn trích dẫn.

        Args:
            question (str): Câu hỏi của người học.
            top_k (int): Số lượng đoạn trích tối đa cần tham khảo.
            where (Optional[Dict[str, Any]]): Điều kiện lọc metadata.
            temperature (float): Nhiệt độ sinh văn bản (mặc định 0.2 chống ảo giác).

        Returns:
            Dict[str, Any]: Kết quả đóng gói chuẩn gồm:
                - question (str): Câu hỏi ban đầu.
                - answer (str): Lời giải thích từ Gia sư AI.
                - sources (List[Dict]): Danh sách các đầu sách và trang đã trích dẫn.
                - raw_chunks (List[Dict]): Toàn bộ thông tin chunks gốc phục vụ debug/kiểm thử.
        """
        logger.info(f"=== BẮT ĐẦU XỬ LÝ RAG PIPELINE CHO: '{question}' ===")

        # 1. Thu hồi tài liệu liên quan (Retrieve)
        chunks = self.retrieve_context(question=question, top_k=top_k, where=where)

        # 2. Bóc tách nguồn trích dẫn sạch sẽ (Sources)
        sources: List[Dict[str, Any]] = []
        for c in chunks:
            meta = c.get("metadata", {})
            sources.append(
                {
                    "book_title": meta.get("book_title", "Không rõ"),
                    "page_number": meta.get("page_number", 0),
                    "unit": meta.get("unit", None),
                    "score": c.get("score", 0.0),
                }
            )

        # 3. Tạo Grounded Prompt
        prompt = self.build_grounded_prompt(question=question, context_chunks=chunks)

        # 4. Gọi LLM sinh câu trả lời (Generate)
        answer = self.llm_service.generate_text(
            prompt=prompt,
            system_instruction=self.system_instruction,
            temperature=temperature,
        )

        logger.info("=== HOÀN THÀNH RAG PIPELINE THÀNH CÔNG ===")
        return {
            "question": question,
            "answer": answer,
            "sources": sources,
            "raw_chunks": chunks,
        }
