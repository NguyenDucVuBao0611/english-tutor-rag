import shutil
import sys
from pathlib import Path

# Đảm bảo thư mục gốc dự án luôn nằm trong sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core.logger import logger
from src.agents.tutor_agent import TutorAgent
from src.services.rag_service import RAGService
from src.tools.rag_tool import GrammarRetrievalTool
from src.vector_store.chroma_store import ChromaVectorStore

TEST_AGENT_DB_DIR = ROOT_DIR / "test_agent_chroma_db"


def clean_test_dir():
    """Dọn dẹp thư mục kiểm thử tạm thời."""
    if TEST_AGENT_DB_DIR.exists():
        shutil.rmtree(TEST_AGENT_DB_DIR, ignore_errors=True)


def setup_agent_environment() -> TutorAgent:
    """Khởi tạo môi trường kho tri thức và Agent để kiểm thử."""
    clean_test_dir()

    vector_store = ChromaVectorStore(
        collection_name="agent_test_knowledge",
        persist_directory=TEST_AGENT_DB_DIR,
    )
    vector_store.reset()

    # Nạp bài học ngữ pháp mẫu
    documents = [
        (
            "The present perfect tense is formed with have/has + past participle (V3). "
            "We use it to talk about experiences up to now, e.g., 'I have visited London twice'. "
            "It is also used with 'since' and 'for'."
        ),
        (
            "The passive voice is formed with subject + appropriate form of 'be' + past participle (V3). "
            "We use the passive voice when the action is more important than who did it. "
            "Example: 'The new bridge was built in 2020 by the workers.'"
        ),
    ]

    metadatas = [
        {"book_title": "English Grammar in Use", "page_number": 14, "unit": 7},
        {"book_title": "Oxford Practice Grammar", "page_number": 42, "unit": 21},
    ]

    ids = ["rule_pres_perfect", "rule_passive"]
    vector_store.add_documents(documents=documents, metadatas=metadatas, ids=ids)

    # Đóng gói RAG Service thành Tool
    rag_service = RAGService(vector_store=vector_store)
    grammar_tool = GrammarRetrievalTool(rag_service=rag_service)

    # Khởi tạo Agent trang bị Tool
    agent = TutorAgent(tools=[grammar_tool])
    return agent


def test_agent_system():
    logger.info("=====================================================================")
    logger.info("🚀 BẮT ĐẦU KIỂM THỬ AUTONOMOUS REACT TUTOR AGENT (NGÀY 7 - MILESTONE 1)")
    logger.info("=====================================================================")

    agent = setup_agent_environment()

    # -----------------------------------------------------------------
    # BÀI TEST 1: CÂU CHÀO HỎI XÃ GIAO (INTENT ROUTING - KHÔNG GỌI TOOL)
    # -----------------------------------------------------------------
    logger.info("\n--- BÀI TEST 1: KIỂM CHỨNG PHÂN LUỒNG Ý ĐỊNH (CHÀO HỎI KHÔNG TRA SÁCH) ---")
    greeting_msg = "Hello teacher! How are you doing today?"
    logger.info(f"Học viên: '{greeting_msg}'")

    res_1 = agent.chat(user_message=greeting_msg)

    logger.info(f"\n🤖 [AGENT TRẢ LỜI]:\n{res_1['answer']}")
    logger.info(f"Các công cụ đã gọi: {res_1['tools_used']}")
    
    # Kiểm tra: Agent phải thông minh nhận ra không cần gọi tool nào!
    assert len(res_1["tools_used"]) == 0, (
        f"Lỗi: Lời chào hỏi thông thường mà Agent lại tự ý gọi tool: {res_1['tools_used']}"
    )
    logger.info("✅ Bài test 1: Intent Routing thông minh, nhận diện câu chào và phản hồi tự nhiên không gọi tool thừa!")

    # -----------------------------------------------------------------
    # BÀI TEST 2: CÂU HỎI NGỮ PHÁP (KÍCH HOẠT TOOL & THỰC THI CHU TRÌNH REACT)
    # -----------------------------------------------------------------
    logger.info("\n--- BÀI TEST 2: CÂU HỎI NGỮ PHÁP (TỰ ĐỘNG KÍCH HOẠT TOOL VÀ TRA SÁCH) ---")
    grammar_msg = "Thầy ơi giải thích giúp em cấu trúc câu Bị động (Passive voice) và cho ví dụ trong sách nhé!"
    logger.info(f"Học viên: '{grammar_msg}'")

    res_2 = agent.chat(user_message=grammar_msg)

    logger.info(f"\n🤖 [AGENT GIẢNG DẠY]:\n{res_2['answer']}")
    logger.info(f"Nhật ký suy luận (Trajectory):")
    for step_info in res_2["thought_trajectory"]:
        logger.info(f"  Bước {step_info.get('step')}: Thought = {step_info.get('thought')[:80]}...")
        if "action" in step_info:
            logger.info(f"         Action = {step_info.get('action')} | Input = {step_info.get('action_input')}")

    logger.info(f"Nguồn sách đã trích dẫn: {res_2['sources']}")

    # Kiểm tra: Agent phải gọi đúng công cụ search_grammar_knowledge
    assert "search_grammar_knowledge" in res_2["tools_used"], "Lỗi: Agent không gọi tool tra cứu ngữ pháp!"
    assert any("Oxford Practice Grammar" in str(s) for s in res_2["sources"]), "Lỗi: Thiếu nguồn trích dẫn từ sách Oxford!"
    assert "built" in res_2["answer"].lower() or "passive" in res_2["answer"].lower(), "Lỗi: Câu trả lời thiếu ví dụ hoặc nội dung trọng tâm!"
    
    logger.info("✅ Bài test 2: Chu trình ReAct (Thought -> Action -> Observation -> Final Answer) hoàn hảo 100%!")

    # Dọn dẹp
    clean_test_dir()
    logger.info("\n🎉 CHÚC MỪNG BẠN! TOÀN BỘ BÀI TEST AGENT ĐÃ PASS - HOÀN THÀNH MILESTONE 1!")


if __name__ == "__main__":
    test_agent_system()
