import shutil
import sys
from pathlib import Path

# Đảm bảo thư mục gốc dự án luôn nằm trong sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core.logger import logger
from src.services.rag_service import RAGService
from src.vector_store.chroma_store import ChromaVectorStore

TEST_RAG_DB_DIR = ROOT_DIR / "test_rag_chroma_db"


def clean_test_dir():
    """Dọn dẹp thư mục cơ sở dữ liệu test tạm thời."""
    if TEST_RAG_DB_DIR.exists():
        shutil.rmtree(TEST_RAG_DB_DIR, ignore_errors=True)


def setup_knowledge_base() -> ChromaVectorStore:
    """Tạo một kho tri thức mẫu gồm các chủ điểm ngữ pháp tiếng Anh chuẩn."""
    clean_test_dir()

    vector_store = ChromaVectorStore(
        collection_name="test_knowledge_base",
        persist_directory=TEST_RAG_DB_DIR,
    )
    vector_store.reset()

    documents = [
        (
            "The present perfect tense is formed with have/has + past participle (V3). "
            "We use it to talk about experiences up to now (e.g., 'I have visited London twice.'). "
            "We also use it with 'since' (point in time) and 'for' (period of time) to describe an action that started in the past and continues to the present."
        ),
        (
            "The passive voice is formed with subject + appropriate form of 'be' + past participle (V3). "
            "We use the passive voice when the action is more important than who did it, or when the agent is unknown. "
            "Example: 'The new bridge was built in 2020.' by the workers."
        ),
        (
            "First conditional is used to talk about real and possible future situations. "
            "Structure: If + present simple, ... will + bare infinitive. "
            "Example: 'If it rains tomorrow, we will cancel the outdoor picnic.'"
        ),
    ]

    metadatas = [
        {"book_title": "English Grammar in Use", "page_number": 14, "unit": 7},
        {"book_title": "Oxford Practice Grammar", "page_number": 42, "unit": 21},
        {"book_title": "English Grammar in Use", "page_number": 76, "unit": 38},
    ]

    ids = ["grammar_rule_pres_perfect", "grammar_rule_passive", "grammar_rule_first_cond"]

    vector_store.add_documents(documents=documents, metadatas=metadatas, ids=ids)
    logger.info(f"Đã nạp thành công {vector_store.count()} bài học vào kho tri thức kiểm thử.")
    return vector_store


def test_rag_pipeline():
    logger.info("=====================================================================")
    logger.info("🚀 BẮT ĐẦU KIỂM THỬ TOÀN DIỆN CORE RAG ENGINE & GROUNDED PROMPTING (NGÀY 6)")
    logger.info("=====================================================================")

    # 1. Khởi tạo kho dữ liệu và Facade Service
    vector_store = setup_knowledge_base()
    rag_service = RAGService(vector_store=vector_store)

    # -----------------------------------------------------------------
    # BÀI TEST 1: CÂU HỎI TRONG PHẠM VI GIÁO TRÌNH (IN-DOMAIN QUESTION)
    # -----------------------------------------------------------------
    logger.info("\n--- BÀI TEST 1: CÂU HỎI NGỮ PHÁP CÓ TRONG GIÁO TRÌNH ---")
    query_1 = "Khi nào tôi nên dùng thì Hiện tại hoàn thành và cấu trúc của nó thế nào?"
    logger.info(f"Học viên hỏi: '{query_1}'")

    response_1 = rag_service.ask(question=query_1, top_k=2)

    logger.info("\n🤖 [GIA SƯ AI TRẢ LỜI]:")
    logger.info(response_1["answer"])

    logger.info("\n📚 [DANH SÁCH NGUỒN TRÍCH DẪN]:")
    for s in response_1["sources"]:
        logger.info(f"  - Sách: {s['book_title']} | Trang: {s['page_number']} | Độ liên quan: {s['score']}")

    # Kiểm tra tính chính xác của câu trả lời
    answer_text = response_1["answer"].lower()
    assert "have" in answer_text or "has" in answer_text, "Lỗi: Câu trả lời thiếu have/has!"
    assert response_1["sources"][0]["book_title"] == "English Grammar in Use", "Lỗi: Không trích dẫn đúng sách!"
    logger.info("✅ Bài test 1: RAG Engine trả lời chuẩn xác và trích dẫn đúng nguồn 100%!")

    # -----------------------------------------------------------------
    # BÀI TEST 2: CÂU HỎI LẠC ĐỀ - KIỂM CHỨNG CHỐNG ẢO GIÁC (REFUSAL POLICY)
    # -----------------------------------------------------------------
    logger.info("\n--- BÀI TEST 2: CÂU HỎI NGOÀI PHẠM VI (THỬ THÁCH ẢO GIÁC) ---")
    query_hallucination = "Công thức nấu món phở bò Hà Nội thơm ngon chuẩn vị truyền thống gồm những bước nào?"
    logger.info(f"Học viên hỏi lạc đề: '{query_hallucination}'")

    response_2 = rag_service.ask(question=query_hallucination, top_k=2)

    logger.info("\n🤖 [GIA SƯ AI PHẢN HỒI KHI BỊ HỎI LẠC ĐỀ]:")
    logger.info(response_2["answer"])

    refusal_text = response_2["answer"].lower()
    # Kiểm tra xem AI có từ chối theo đúng kỷ luật thép không (không được bịa công thức nấu phở)
    is_refused = any(
        kw in refusal_text for kw in ["chưa có thông tin", "không có", "giáo trình", "tài liệu", "tiếc"]
    )
    assert is_refused, "Lỗi: AI đã không từ chối câu hỏi ngoài phạm vi tài liệu!"
    logger.info("✅ Bài test 2: Grounded Prompting kích hoạt Refusal Policy triệt tiêu ảo giác thành công!")

    # -----------------------------------------------------------------
    # BÀI TEST 3: TRÍCH XUẤT NGỮ CẢNH ĐỘC LẬP (SẴN SÀNG CHO AGENT TOOL NGÀY 7)
    # -----------------------------------------------------------------
    logger.info("\n--- BÀI TEST 3: TRUY VẤN NGỮ CẢNH ĐỘC LẬP CHO AGENT TOOL ---")
    tool_chunks = rag_service.retrieve_context(question="If it rains tomorrow", top_k=1)
    assert len(tool_chunks) == 1
    assert "First conditional" in tool_chunks[0]["document"]
    logger.info(f"Đoạn trích lấy về cho Tool: \"{tool_chunks[0]['document'][:60]}...\"")
    logger.info("✅ Bài test 3: Giao diện retrieve_context đã sẵn sàng để Ngày 7 bọc thành Agent Tool!")

    # Dọn dẹp
    clean_test_dir()
    logger.info("\n🎉 TOÀN BỘ CÁC BÀI KIỂM THỬ RAG ENGINE NGÀY 6 ĐÃ VƯỢT QUA XUẤT SẮC!")


if __name__ == "__main__":
    test_rag_pipeline()
