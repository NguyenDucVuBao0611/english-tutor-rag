import re
from pathlib import Path
from typing import List, Union
from pydantic import BaseModel, Field
from pypdf import PdfReader

from src.core.logger import logger


class DocumentMetadata(BaseModel):
    """Khuôn dữ liệu chứa thông tin nguồn gốc (Metadata) của trang tài liệu."""
    source: str = Field(description="Tên file hoặc nguồn gốc của tài liệu")
    page_number: int = Field(ge=1, description="Số thứ tự trang trong tài liệu (bắt đầu từ 1)")
    total_pages: int = Field(ge=1, description="Tổng số trang của tài liệu")
    char_count: int = Field(ge=0, description="Số lượng ký tự văn bản của trang sau khi làm sạch")


class DocumentPage(BaseModel):
    """Khuôn dữ liệu biểu diễn một trang tài liệu đã được trích xuất và chuẩn hóa."""
    content: str = Field(description="Nội dung văn bản tiếng Anh đã được làm sạch")
    metadata: DocumentMetadata = Field(description="Metadata nguồn gốc tương ứng của trang")


class DocumentService:
    """Service nghiệp vụ chịu trách nhiệm nạp (Ingest) và làm sạch tài liệu PDF."""

    @staticmethod
    def clean_text(text: str) -> str:
        """Làm sạch và chuẩn hóa văn bản tiếng Anh trích xuất từ PDF.

        Quy trình xử lý:
        1. Khử ký tự điều khiển rác của PDF (NULL byte, Form Feed).
        2. Khử hiện tượng gạch nối ngắt dòng (Hyphenation): ghép 'pre-\\nsent' thành 'present'.
        3. Chuẩn hóa khoảng trắng ngang (nhiều dấu cách, tab liên tiếp -> 1 dấu cách).
        4. Rút gọn các dòng trống thừa thãi (tối đa 2 dấu xuống dòng liên tiếp).
        5. Xóa khoảng trắng ở đầu và cuối chuỗi.

        Args:
            text (str): Chuỗi văn bản thô từ PDF.

        Returns:
            str: Chuỗi văn bản sạch, chuẩn hóa ngữ liệu.
        """
        if not text:
            return ""

        # 1. Loại bỏ các ký tự điều khiển lạ sinh ra từ định dạng nhị phân PDF
        cleaned = text.replace("\x00", "").replace("\x0c", "")

        # 2. Xử lý Hyphenation: ghép các từ tiếng Anh bị bẻ đôi ở cuối dòng
        # Ví dụ: "fundamen-\n  tal" -> "fundamental"
        cleaned = re.sub(r"(\b[a-zA-Z]+)-\s*\n\s*([a-zA-Z]+\b)", r"\1\2", cleaned)

        # 3. Chuẩn hóa các dấu cách hoặc tab liên tiếp thành một dấu cách đơn
        cleaned = re.sub(r"[ \t]+", " ", cleaned)

        # 4. Rút gọn nhiều dấu xuống dòng liên tiếp thành tối đa 2 dấu xuống dòng (phân đoạn)
        cleaned = re.sub(r"\n\s*\n\s*\n+", "\n\n", cleaned)

        # 5. Cắt tỉa khoảng trắng ở đầu và cuối
        return cleaned.strip()

    def extract_from_pdf(self, file_path: Union[str, Path]) -> List[DocumentPage]:
        """Đọc toàn bộ các trang từ file PDF và trả về danh sách DocumentPage chuẩn hóa.

        Args:
            file_path (Union[str, Path]): Đường dẫn tới file PDF cần trích xuất.

        Returns:
            List[DocumentPage]: Danh sách các trang tài liệu đã được chuẩn hóa và gắn metadata.

        Raises:
            FileNotFoundError: Khi không tìm thấy file PDF tại đường dẫn chỉ định.
            Exception: Khi file PDF bị hỏng hoặc không thể giải mã.
        """
        path = Path(file_path).resolve()
        if not path.exists():
            error_msg = f"Không tìm thấy file PDF tại: {path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        logger.info(f"Bắt đầu trích xuất PDF: {path.name}")

        try:
            reader = PdfReader(str(path))
            total_pages = len(reader.pages)
            logger.info(f"Tổng số trang phát hiện được: {total_pages} trang")

            pages: List[DocumentPage] = []

            for idx, page in enumerate(reader.pages):
                page_number = idx + 1
                raw_text = page.extract_text() or ""
                cleaned_text = self.clean_text(raw_text)

                if not cleaned_text:
                    logger.warning(f"[{path.name}] Trang {page_number}/{total_pages} bị trống hoặc không có chữ.")
                    continue

                page_doc = DocumentPage(
                    content=cleaned_text,
                    metadata=DocumentMetadata(
                        source=path.name,
                        page_number=page_number,
                        total_pages=total_pages,
                        char_count=len(cleaned_text),
                    ),
                )
                pages.append(page_doc)

            logger.info(f"Hoàn thành trích xuất [{path.name}]: Thu được {len(pages)} trang hợp lệ.")
            return pages

        except Exception as e:
            logger.error(f"Lỗi bất ngờ khi xử lý file PDF [{path.name}]: {str(e)}")
            raise
