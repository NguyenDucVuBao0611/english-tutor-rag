from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel, Field

from src.core.logger import logger
from src.services.document_service import DocumentPage


class ChunkMetadata(BaseModel):
    """Metadata nguồn gốc gắn liền với từng đoạn cắt (Chunk)."""
    source: str = Field(description="Tên file hoặc nguồn gốc cuốn sách")
    page_number: int = Field(ge=1, description="Số thứ tự trang gốc của sách")
    chunk_index: int = Field(ge=0, description="Chỉ số thứ tự của chunk trong toàn bộ tài liệu")
    char_count: int = Field(ge=0, description="Số lượng ký tự trong chunk")


class Chunk(BaseModel):
    """Khuôn dữ liệu biểu diễn một đoạn văn bản nhỏ hoàn chỉnh để đưa vào Vector DB."""
    content: str = Field(description="Nội dung ngữ nghĩa của đoạn văn bản")
    metadata: ChunkMetadata = Field(description="Metadata truy vết của đoạn văn bản")


# =====================================================================
# 1. STRATEGY PATTERN: INTERFACE & CONCRETE STRATEGIES
# =====================================================================

class BaseChunker(ABC):
    """Interface trừu tượng cho các chiến lược cắt văn bản (Strategy Pattern)."""

    @abstractmethod
    def split_text(self, text: str) -> List[str]:
        """Chia nhỏ một chuỗi văn bản thành danh sách các chuỗi ngắn hơn."""
        pass


class RecursiveCharacterChunker(BaseChunker):
    """Chiến lược cắt văn bản đệ quy (Recursive Character Splitting).

    Ưu tiên giữ trọn vẹn ngữ nghĩa bằng cách cắt lần lượt theo các dấu phân cách:
    1. Đoạn văn ('\\n\\n')
    2. Dòng ('\\n')
    3. Kết thúc câu ('. ')
    4. Từ ngữ (' ')
    5. Ký tự đơn lẻ ('')
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        if chunk_overlap >= chunk_size:
            raise ValueError(f"chunk_overlap ({chunk_overlap}) phải nhỏ hơn chunk_size ({chunk_size})!")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = ["\n\n", "\n", ". ", " ", ""]

    def _split_recursive(self, text: str, separators: List[str]) -> List[str]:
        """Hàm đệ quy băm nhỏ văn bản theo danh sách dấu phân cách."""
        if not text:
            return []

        # Nếu văn bản đã đủ nhỏ hơn hoặc bằng chunk_size thì không cần băm nữa
        if len(text) <= self.chunk_size:
            return [text.strip()] if text.strip() else []

        # Chọn dấu phân cách đầu tiên còn khả dụng
        separator = separators[-1]
        for sep in separators:
            if sep in text:
                separator = sep
                break

        # Tách chuỗi theo dấu phân cách đã chọn
        splits = text.split(separator) if separator else list(text)

        # Lấy danh sách dấu phân cách kế tiếp cho các bước đệ quy sâu hơn
        remaining_separators = separators[separators.index(separator) + 1 :] if separator in separators else []

        chunks: List[str] = []
        current_chunk: List[str] = []
        current_length = 0

        for piece in splits:
            piece_len = len(piece) + (len(separator) if current_chunk else 0)

            if current_length + piece_len <= self.chunk_size:
                current_chunk.append(piece)
                current_length += piece_len
            else:
                # Nếu một mẩu văn bản đơn lẻ vẫn lớn hơn chunk_size, đệ quy băm tiếp bằng dấu phân cách nhỏ hơn
                if piece_len > self.chunk_size and remaining_separators:
                    sub_pieces = self._split_recursive(piece, remaining_separators)
                    for sp in sub_pieces:
                        if current_length + len(sp) <= self.chunk_size:
                            current_chunk.append(sp)
                            current_length += len(sp)
                        else:
                            if current_chunk:
                                chunks.append(separator.join(current_chunk).strip())
                            current_chunk = [sp]
                            current_length = len(sp)
                else:
                    if current_chunk:
                        chunks.append(separator.join(current_chunk).strip())
                    current_chunk = [piece]
                    current_length = len(piece)

        if current_chunk:
            chunks.append(separator.join(current_chunk).strip())

        return [c for c in chunks if c]

    def _add_overlap(self, chunks: List[str]) -> List[str]:
        """Tạo sự gối đầu (overlap) giữa các chunk liền kề để tránh mất mạch ý."""
        if len(chunks) <= 1 or self.chunk_overlap == 0:
            return chunks

        overlapped_chunks: List[str] = [chunks[0]]

        for i in range(1, len(chunks)):
            prev_chunk = chunks[i - 1]
            curr_chunk = chunks[i]

            # Lấy phần đuôi của chunk trước làm đầu cho chunk hiện tại
            overlap_prefix = prev_chunk[-self.chunk_overlap :] if len(prev_chunk) >= self.chunk_overlap else prev_chunk
            combined = f"{overlap_prefix}... {curr_chunk}"
            overlapped_chunks.append(combined)

        return overlapped_chunks

    def split_text(self, text: str) -> List[str]:
        """Thực thi phân đoạn văn bản kèm gối đầu."""
        raw_chunks = self._split_recursive(text, self.separators)
        return self._add_overlap(raw_chunks)


# =====================================================================
# 2. CHUNKER SERVICE (QUẢN LÝ NGHIỆP VỤ PHÂN ĐOẠN)
# =====================================================================

class ChunkerService:
    """Service điều phối nghiệp vụ phân đoạn tài liệu, hỗ trợ Strategy Pattern."""

    def __init__(self, strategy: Optional[BaseChunker] = None):
        # Mặc định sử dụng chiến lược RecursiveCharacterChunker
        self.strategy = strategy or RecursiveCharacterChunker(chunk_size=500, chunk_overlap=50)

    def set_strategy(self, strategy: BaseChunker) -> None:
        """Cho phép hoán đổi chiến lược chunking linh hoạt khi đang chạy (Strategy Pattern)."""
        self.strategy = strategy
        logger.info(f"Đã chuyển đổi chiến lược Chunking sang: {strategy.__class__.__name__}")

    def chunk_document_pages(self, pages: List[DocumentPage]) -> List[Chunk]:
        """Nhận danh sách DocumentPage từ Ngày 2 và băm nhỏ thành các Chunk có metadata.

        Args:
            pages (List[DocumentPage]): Danh sách các trang đã được trích xuất và làm sạch.

        Returns:
            List[Chunk]: Danh sách các chunk hoàn chỉnh sẵn sàng cho Vector Database.
        """
        logger.info(f"Bắt đầu phân đoạn {len(pages)} trang tài liệu...")
        all_chunks: List[Chunk] = []
        global_chunk_idx = 0

        for page in pages:
            text_chunks = self.strategy.split_text(page.content)

            for text_chunk in text_chunks:
                chunk_obj = Chunk(
                    content=text_chunk,
                    metadata=ChunkMetadata(
                        source=page.metadata.source,
                        page_number=page.metadata.page_number,
                        chunk_index=global_chunk_idx,
                        char_count=len(text_chunk),
                    ),
                )
                all_chunks.append(chunk_obj)
                global_chunk_idx += 1

        logger.info(f"Hoàn thành phân đoạn: Tạo ra tổng cộng {len(all_chunks)} chunks.")
        return all_chunks
