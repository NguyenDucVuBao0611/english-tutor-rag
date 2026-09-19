import sys
from pathlib import Path

# Đảm bảo thư mục gốc dự án luôn nằm trong sys.path để import được package src
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core.logger import logger
from src.services.document_service import DocumentService

DATA_DIR = ROOT_DIR / "data" / "raw"


def test_clean_text_logic():
    """Kiểm tra tính chính xác của thuật toán làm sạch văn bản tiếng Anh."""
    logger.info("=== BÀI TEST 1: KIỂM THỬ THUẬT TOÁN CLEAN_TEXT ===")

    sample_raw_text = (
        "In English grammar, the pre-\n"
        "sent perfect tense is fundamen-\n"
        "tal for describing past experiences.\n\n\n\n"
        "This    sentence   has   weird    spaces."
    )

    cleaned = DocumentService.clean_text(sample_raw_text)

    # 1. Kiểm tra xem từ 'present' và 'fundamental' có được ghép liền lại không
    assert "present" in cleaned, "Lỗi: Chưa khử được gạch nối ở chữ 'pre-\\nsent'"
    assert "fundamental" in cleaned, "Lỗi: Chưa khử được gạch nối ở chữ 'fundamen-\\ntal'"

    # 2. Kiểm tra xem các khoảng trắng thừa có được gộp thành 1 khoảng trắng không
    assert "This sentence has weird spaces." in cleaned, "Lỗi: Chưa chuẩn hóa khoảng trắng thừa"

    logger.info("✅ Bài test clean_text đạt kết quả xuất sắc 100%!")
    logger.info(f"Kết quả sau làm sạch:\n---\n{cleaned}\n---")


def test_real_pdf_ingestion():
    """Kiểm thử nạp trực tiếp một file PDF giáo trình thực tế trong thư mục data/raw."""
    logger.info("=== BÀI TEST 2: KIỂM THỬ ĐỌC VÀ CHUẨN HÓA SÁCH PDF THẬT ===")

    pdf_filename = "Ngữ pháp tiếng Anh cơ bản - IELTS Fighter.pdf"
    pdf_path = DATA_DIR / pdf_filename

    if not pdf_path.exists():
        logger.warning(f"Không tìm thấy file mẫu tại {pdf_path}. Hãy kiểm tra lại thư mục data/raw!")
        return

    service = DocumentService()
    pages = service.extract_from_pdf(pdf_path)

    assert len(pages) > 0, "Lỗi: Không trích xuất được trang nào từ PDF!"

    logger.info(f"✅ Đọc thành công file: {pdf_filename}")
    logger.info(f"Tổng số trang hợp lệ trích xuất được: {len(pages)} trang")

    # In ra thông tin chi tiết của 2 trang đầu tiên để kiểm tra metadata
    for i in range(min(2, len(pages))):
        page = pages[i]
        logger.info(f"--- TRANG {page.metadata.page_number} ---")
        logger.info(f"Tên nguồn (source): {page.metadata.source}")
        logger.info(f"Số ký tự (char_count): {page.metadata.char_count}")
        preview = page.content[:200].replace("\n", " ")
        logger.info(f"Đoạn trích 200 ký tự đầu: \"{preview}...\"")

    logger.info("✅ Toàn bộ bài test Ngày 2 hoàn tất thành công!")


if __name__ == "__main__":
    test_clean_text_logic()
    print()
    test_real_pdf_ingestion()
