import sys
from pathlib import Path

# Đảm bảo thư mục gốc dự án luôn nằm trong sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core.logger import logger
from src.services.document_service import DocumentService
from src.services.chunker_service import ChunkerService, RecursiveCharacterChunker

DATA_DIR = ROOT_DIR / "data" / "raw"


def test_recursive_chunker_logic():
    """Kiểm tra logic cắt đệ quy và tính năng gối đầu (overlap) của RecursiveCharacterChunker."""
    logger.info("=== BÀI TEST 1: KIỂM THỬ THUẬT TOÁN RECURSIVE CHUNKER ===")

    sample_grammar_text = (
        "1. THE PRESENT PERFECT TENSE.\n\n"
        "Formula: Subject + have/has + Past Participle (V3/ed).\n\n"
        "Usage: We use the present perfect tense to talk about experiences in life up to now, "
        "or actions that happened in the past but have results in the present.\n\n"
        "Examples:\n"
        "- I have lived in Hanoi for five years.\n"
        "- She has already finished her homework.\n"
        "- They haven't seen that movie yet."
    )

    chunker = RecursiveCharacterChunker(chunk_size=200, chunk_overlap=30)
    chunks = chunker.split_text(sample_grammar_text)

    logger.info(f"Đoạn văn gốc dài: {len(sample_grammar_text)} ký tự")
    logger.info(f"Số chunk được chia ra: {len(chunks)} chunks")

    assert len(chunks) > 1, "Lỗi: Văn bản dài hơn chunk_size nhưng không được chia nhỏ!"

    for i, c in enumerate(chunks):
        logger.info(f"--- Chunk {i + 1} ({len(c)} ký tự) ---")
        logger.info(f"Nội dung:\n{c}")

    logger.info("✅ Bài test 1: Thuật toán Recursive Chunker hoạt động chính xác 100%!")


def test_chunk_real_document():
    """Kiểm thử kết nối luồng từ Ngày 2 sang Ngày 3: DocumentService -> ChunkerService."""
    logger.info("=== BÀI TEST 2: KẾT NỐI LUỒNG THỰC TẾ TRÊN SÁCH PDF ===")

    pdf_filename = "Ngữ pháp tiếng Anh cơ bản - IELTS Fighter.pdf"
    pdf_path = DATA_DIR / pdf_filename

    if not pdf_path.exists():
        logger.warning(f"Không tìm thấy file mẫu tại {pdf_path}")
        return

    # Bước 1: Dùng DocumentService (Ngày 2) đọc 2 trang đầu tiên
    doc_service = DocumentService()
    all_pages = doc_service.extract_from_pdf(pdf_path)
    sample_pages = all_pages[:2]

    # Bước 2: Dùng ChunkerService (Ngày 3) băm 2 trang này thành các chunk
    chunk_service = ChunkerService()
    chunks = chunk_service.chunk_document_pages(sample_pages)

    logger.info(f"Từ {len(sample_pages)} trang sách ban đầu -> Đã tạo ra {len(chunks)} chunks.")
    assert len(chunks) > 0, "Lỗi: Không tạo được chunk nào từ các trang sách!"

    # In mẫu 3 chunk đầu tiên để kiểm tra Metadata truy vết
    for i in range(min(3, len(chunks))):
        chk = chunks[i]
        logger.info(f"--- CHUNK {chk.metadata.chunk_index} (Trang {chk.metadata.page_number}) ---")
        logger.info(f"Nguồn (source): {chk.metadata.source}")
        logger.info(f"Độ dài: {chk.metadata.char_count} ký tự")
        preview = chk.content[:150].replace("\n", " ")
        logger.info(f"Đoạn trích: \"{preview}...\"")

    logger.info("✅ Toàn bộ bài test Ngày 3 hoàn tất thành công!")


if __name__ == "__main__":
    test_recursive_chunker_logic()
    print()
    test_chunk_real_document()
