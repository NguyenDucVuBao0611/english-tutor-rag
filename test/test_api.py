"""Kịch bản kiểm thử toàn diện FastAPI Backend với TestClient (Ngày 8)."""

import io
import shutil
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Đảm bảo đường dẫn gốc nằm trong sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.api.dependencies import (
    get_grammar_tool,
    get_rag_service,
    get_tutor_agent,
    get_vector_store,
    reset_dependencies,
)
from src.core.logger import logger
from src.main_api import app
from src.vector_store.chroma_store import ChromaVectorStore

TEST_API_DB_DIR = ROOT_DIR / "test_api_chroma_db"


def clean_test_api_dir():
    """Dọn dẹp thư mục kiểm thử Vector DB tạm thời."""
    if TEST_API_DB_DIR.exists():
        shutil.rmtree(TEST_API_DB_DIR, ignore_errors=True)


def override_vector_store():
    """Hàm override Dependency: Ép API sử dụng kho ChromaDB kiểm thử cô lập."""
    return ChromaVectorStore(
        collection_name="api_test_collection",
        persist_directory=TEST_API_DB_DIR,
    )


def setup_test_environment():
    """Khởi tạo môi trường kiểm thử và Dependency Override."""
    clean_test_api_dir()
    reset_dependencies()

    # Nạp kho DB tạm thời
    test_store = override_vector_store()
    test_store.reset()

    # Nạp 1 bài học ngữ pháp mẫu để kiểm thử RAG qua API
    test_store.add_documents(
        documents=[
            (
                "Conditionals Type 1: If + present simple, will + base verb. "
                "Used for real and possible situations in the present or future. "
                "Example: 'If it rains tomorrow, we will stay at home.'"
            )
        ],
        metadatas=[{"book_title": "Cambridge Grammar in Use", "page_number": 76, "unit": 38}],
        ids=["rule_cond_type_1"],
    )

    # Đăng ký Dependency Override của FastAPI
    app.dependency_overrides[get_vector_store] = lambda: test_store


def teardown_test_environment():
    """Dọn dẹp sau khi kiểm thử xong."""
    app.dependency_overrides.clear()
    reset_dependencies()
    clean_test_api_dir()


def test_full_api_suite():
    """Chạy toàn bộ chuỗi kiểm thử API tự động."""
    logger.info("====================================================================")
    logger.info("🧪 BẮT ĐẦU KIỂM THỬ TOÀN BỘ FASTAPI BACKEND (NGÀY 8)")
    logger.info("====================================================================")

    setup_test_environment()
    client = TestClient(app)

    # -------------------------------------------------------------
    # BÀI TEST 1: KIỂM TRA ROOT & HEALTH CHECK
    # -------------------------------------------------------------
    logger.info("\n--- BÀI TEST 1: KIỂM TRA ROOT VÀ HEALTH CHECK ENDPOINT ---")
    res_root = client.get("/")
    assert res_root.status_code == 200, f"Root endpoint lỗi: {res_root.text}"
    logger.info(f"✅ Root endpoint phản hồi: {res_root.json()['app_name']}")

    res_health = client.get("/health")
    assert res_health.status_code == 200, f"Health endpoint lỗi: {res_health.text}"
    health_data = res_health.json()
    assert health_data["status"] == "healthy"
    assert health_data["chroma_status"] == "connected"
    logger.info(f"✅ Health endpoint kiểm tra thành công: {health_data}")

    # -------------------------------------------------------------
    # BÀI TEST 2: KIỂM CHỨNG TỰ ĐỘNG BẮT LỖI DỮ LIỆU (VALIDATION 422)
    # -------------------------------------------------------------
    logger.info("\n--- BÀI TEST 2: KIỂM CHỨNG BẮT LỖI PYDANTIC VALIDATION (HTTP 422) ---")
    # Gửi body rỗng hoặc thiếu trường 'message'
    res_invalid = client.post("/api/v1/agent/chat", json={})
    assert res_invalid.status_code == 422, f"Kỳ vọng 422 nhưng nhận được: {res_invalid.status_code}"
    logger.info("✅ Pydantic & FastAPI chặn thành công gói tin sai định dạng với mã lỗi 422 Unprocessable Entity!")

    # -------------------------------------------------------------
    # BÀI TEST 3: GỌI CHAT API - CÂU CHÀO HỎI (INTENT ROUTING)
    # -------------------------------------------------------------
    logger.info("\n--- BÀI TEST 3: CHAT API VỚI CÂU CHÀO HỎI (INTENT ROUTING) ---")
    greeting_payload = {"message": "Hello teacher! Good morning!", "max_iterations": 2}
    res_chat_greeting = client.post("/api/v1/agent/chat", json=greeting_payload)
    assert res_chat_greeting.status_code == 200, f"Chat API lỗi: {res_chat_greeting.text}"

    greet_data = res_chat_greeting.json()
    logger.info(f"🤖 [Agent trả lời qua API]: {greet_data['answer']}")
    logger.info(f"Tools đã dùng: {greet_data['tools_used']} | Thời gian: {greet_data['execution_time_seconds']}s")
    assert len(greet_data["tools_used"]) == 0, "Lỗi: Câu chào hỏi mà Agent lại gọi tool!"
    logger.info("✅ Chat API chào hỏi thành công, không kích hoạt tool thừa!")

    # -------------------------------------------------------------
    # BÀI TEST 4: TẢI LÊN TÀI LIỆU MỚI QUA UPLOAD API
    # -------------------------------------------------------------
    logger.info("\n--- BÀI TEST 4: TẢI LÊN VÀ NẠP TÀI LIỆU MỚI QUA /documents/upload ---")
    sample_text = (
        "Modal verbs in English: Can, Could, May, Might, Must, Should. "
        "We use 'must' for strong obligations, e.g., 'You must wear a helmet.' "
        "We use 'should' for advice, e.g., 'You should sleep early.'"
    )
    file_bytes = io.BytesIO(sample_text.encode("utf-8"))
    files = {"file": ("modal_verbs_lesson.txt", file_bytes, "text/plain")}

    res_upload = client.post("/api/v1/documents/upload", files=files)
    assert res_upload.status_code == 201, f"Upload API lỗi: {res_upload.text}"

    upload_data = res_upload.json()
    logger.info(f"📄 [Upload API phản hồi]: {upload_data}")
    assert upload_data["status"] == "success"
    assert upload_data["total_chunks"] >= 1
    logger.info("✅ Upload API hoạt động hoàn hảo, đã nạp tài liệu vào ChromaDB!")

    # -------------------------------------------------------------
    # BÀI TEST 5: GỌI CHAT API VỚI CÂU HỎI NGỮ PHÁP (KÍCH HOẠT REACT & TOOL)
    # -------------------------------------------------------------
    logger.info("\n--- BÀI TEST 5: CHAT API HỎI NGỮ PHÁP (KÍCH HOẠT REACT VÀ TRÍCH DẪN) ---")
    grammar_payload = {
        "message": "Thầy ơi giải thích giúp em câu điều kiện loại 1 (Conditional Type 1) và cho ví dụ trong sách nhé!",
        "max_iterations": 4,
    }
    res_chat_grammar = client.post("/api/v1/agent/chat", json=grammar_payload)
    assert res_chat_grammar.status_code == 200, f"Chat API lỗi: {res_chat_grammar.text}"

    grammar_data = res_chat_grammar.json()
    logger.info(f"\n🤖 [Agent giảng giải qua API]:\n{grammar_data['answer']}")
    logger.info(f"Tools đã kích hoạt: {grammar_data['tools_used']}")
    logger.info(f"Nguồn sách trích dẫn: {grammar_data['sources']}")
    logger.info(f"Vết suy luận (Trajectory): {len(grammar_data['thought_trajectory'])} bước")

    assert "search_grammar_knowledge" in grammar_data["tools_used"], "Agent phải kích hoạt search_grammar_knowledge!"
    assert len(grammar_data["sources"]) > 0, "Phải có ít nhất 1 nguồn sách trích dẫn!"
    logger.info("✅ Chat API câu hỏi ngữ pháp hoàn thành xuất sắc!")

    teardown_test_environment()
    logger.info("\n🎉 CHÚC MỪNG BẠN! TOÀN BỘ 5 BÀI TEST FASTAPI BACKEND ĐÃ PASS 100%!")


if __name__ == "__main__":
    test_full_api_suite()
