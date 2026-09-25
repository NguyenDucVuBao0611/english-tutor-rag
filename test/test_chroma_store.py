import shutil
import sys
from pathlib import Path

# Đảm bảo thư mục gốc dự án luôn nằm trong sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core.logger import logger
from src.vector_store.chroma_store import ChromaVectorStore

# Đường dẫn thư mục lưu trữ test tạm thời
TEST_DB_DIR = ROOT_DIR / "test_chroma_db"


def clean_test_dir():
    """Dọn dẹp thư mục kiểm thử nếu đã tồn tại trước đó."""
    if TEST_DB_DIR.exists():
        shutil.rmtree(TEST_DB_DIR, ignore_errors=True)


def test_chroma_pipeline():
    logger.info("=====================================================================")
    logger.info("🚀 BẮT ĐẦU KIỂM THỬ TOÀN DIỆN CHROMADB VECTOR STORE (NGÀY 5)")
    logger.info("=====================================================================")

    clean_test_dir()

    # Dữ liệu mẫu đại diện cho các bài học ngữ pháp tiếng Anh
    sample_documents = [
        "The present perfect tense is formed with have/has + past participle (V3). It is used for life experiences.",
        "The past continuous tense uses was/were + V-ing to describe actions happening at a specific time in the past.",
        "Future simple with 'will' is used for promises, offers, and decisions made at the moment of speaking.",
        "Use 'since' with a specific point in time (e.g., since 2010), and 'for' with a duration of time (e.g., for 5 years).",
        "Passive voice is formed with 'be' + past participle (V3). It emphasizes the action rather than the doer.",
    ]

    sample_metadatas = [
        {"book_title": "English Grammar in Use", "page_number": 14, "unit": 7, "topic": "tenses"},
        {"book_title": "English Grammar in Use", "page_number": 18, "unit": 9, "topic": "tenses"},
        {"book_title": "English Grammar in Use", "page_number": 24, "unit": 12, "topic": "tenses"},
        {"book_title": "Oxford Practice Grammar", "page_number": 30, "unit": 15, "topic": "prepositions"},
        {"book_title": "Oxford Practice Grammar", "page_number": 42, "unit": 21, "topic": "voice"},
    ]

    sample_ids = [f"grammar_chunk_{i+1}" for i in range(len(sample_documents))]

    # -----------------------------------------------------------------
    # BÀI TEST 1: KHỞI TẠO VÀ NẠP DỮ LIỆU (INGESTION & COUNT)
    # -----------------------------------------------------------------
    logger.info("\n--- BÀI TEST 1: KHỞI TẠO VÀ THÊM DỮ LIỆU VÀO CHROMADB ---")
    store = ChromaVectorStore(
        collection_name="test_english_tutor",
        persist_directory=TEST_DB_DIR,
    )

    # Đảm bảo ban đầu rỗng
    store.reset()
    assert store.count() == 0, "Lỗi: Collection sau khi reset không rỗng!"

    # Thêm dữ liệu vào
    added_ids = store.add_documents(
        documents=sample_documents,
        metadatas=sample_metadatas,
        ids=sample_ids,
    )

    logger.info(f"Đã thêm các ID: {added_ids}")
    logger.info(f"Tổng số bản ghi trong ChromaDB hiện tại: {store.count()}")
    assert store.count() == len(sample_documents), "Lỗi: Số lượng bản ghi trong ChromaDB không khớp!"
    logger.info("✅ Bài test 1: Ingestion và Count thành công 100%!")

    # -----------------------------------------------------------------
    # BÀI TEST 2: TRUY VẤN NGỮ NGHĨA (SEMANTIC SEARCH)
    # -----------------------------------------------------------------
    logger.info("\n--- BÀI TEST 2: TRUY VẤN NGỮ NGHĨA TOP-K BẰNG CÂU HỎI TỰ NHIÊN ---")
    user_query = "How to talk about things I have experienced in my life?"
    logger.info(f"Câu hỏi của học viên: '{user_query}'")

    results = store.similarity_search(query=user_query, top_k=2)

    logger.info(f"Tìm thấy {len(results)} kết quả liên quan nhất:")
    for rank, res in enumerate(results, 1):
        logger.info(
            f"  Top {rank} | Điểm tương đồng: {res['score']:.4f} (Distance: {res['distance']:.4f})\n"
            f"        Nguồn: [{res['metadata']['book_title']} - Trang {res['metadata']['page_number']}]\n"
            f"        Nội dung: \"{res['document'][:80]}...\""
        )

    # Kỳ vọng đoạn 1 (Present Perfect) phải là Top 1
    assert results[0]["id"] == "grammar_chunk_1", "Lỗi: Đoạn Hiện tại hoàn thành không đứng Top 1!"
    logger.info("✅ Bài test 2: Semantic Search xếp hạng chính xác 100%!")

    # -----------------------------------------------------------------
    # BÀI TEST 3: LỌC NÂNG CAO BẰNG METADATA (METADATA FILTERING)
    # -----------------------------------------------------------------
    logger.info("\n--- BÀI TEST 3: TÌM KIẾM KẾT HỢP BỘ LỌC METADATA ---")
    query_grammar = "How to use past participle V3?"
    filter_oxford = {"book_title": "Oxford Practice Grammar"}

    logger.info(f"Câu hỏi: '{query_grammar}' với điều kiện: {filter_oxford}")
    filtered_results = store.similarity_search(
        query=query_grammar,
        top_k=2,
        where=filter_oxford,
    )

    logger.info(f"Tìm thấy {len(filtered_results)} kết quả phù hợp bộ lọc:")
    for rank, res in enumerate(filtered_results, 1):
        logger.info(
            f"  Top {rank} | Sách: {res['metadata']['book_title']} | Điểm: {res['score']:.4f}\n"
            f"        Nội dung: \"{res['document'][:80]}...\""
        )
        assert res["metadata"]["book_title"] == "Oxford Practice Grammar", (
            f"Lỗi: Kết quả không thuộc sách Oxford: {res['metadata']}"
        )

    logger.info("✅ Bài test 3: Metadata Filtering hoạt động chính xác tuyệt đối!")

    # -----------------------------------------------------------------
    # BÀI TEST 4: KIỂM CHỨNG TÍNH LƯU TRỮ BỀN VỮNG (PERSISTENCE TEST)
    # -----------------------------------------------------------------
    logger.info("\n--- BÀI TEST 4: KIỂM CHỨNG LƯU TRỮ BỀN VỮNG XUỐNG Ổ CỨNG ---")
    # Khởi tạo một đối tượng store hoàn toàn mới trỏ vào cùng thư mục
    logger.info("Giả lập tắt ứng dụng và khởi động lại Client mới kết nối vào thư mục...")
    new_store_session = ChromaVectorStore(
        collection_name="test_english_tutor",
        persist_directory=TEST_DB_DIR,
    )

    reloaded_count = new_store_session.count()
    logger.info(f"Số lượng bản ghi tự động nạp từ ổ cứng: {reloaded_count}")
    assert reloaded_count == len(sample_documents), (
        f"Lỗi: Dữ liệu bị mất sau khi mở lại session! (Kỳ vọng: {len(sample_documents)}, Thực tế: {reloaded_count})"
    )

    # Thử search ngay trên session mới mà không cần nạp lại dữ liệu
    quick_test = new_store_session.similarity_search(query="duration of time", top_k=1)
    logger.info(f"Kết quả truy vấn tức thì từ đĩa: \"{quick_test[0]['document'][:60]}...\"")
    assert "since" in quick_test[0]["document"] or "for" in quick_test[0]["document"], (
        "Lỗi: Truy vấn dữ liệu từ đĩa không chính xác!"
    )
    logger.info("✅ Bài test 4: Tính bền vững (Persistence) hoạt động hoàn hảo!")

    # Dọn dẹp sau khi kiểm thử xong
    clean_test_dir()
    logger.info("\n🎉 TOÀN BỘ 4 BÀI TEST ĐÃ VƯỢT QUA XUẤT SẮC!")


if __name__ == "__main__":
    test_chroma_pipeline()
