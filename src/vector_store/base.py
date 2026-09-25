from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseVectorStore(ABC):
    """Interface trừu tượng quy định hợp đồng cho mọi Vector Store Repository trong hệ thống.
    
    Tuân thủ nguyên lý Dependency Inversion (SOLID) và Repository Pattern.
    Cho phép hệ thống linh hoạt thay đổi từ ChromaDB sang Qdrant, Pinecone hoặc Milvus
    mà không cần sửa đổi bất kỳ dòng mã nào ở tầng Business Logic (Service Layer).
    """

    @abstractmethod
    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """Lưu trữ danh sách các đoạn văn bản (chunks) và metadata vào Vector Database.

        Args:
            documents (List[str]): Danh sách các đoạn văn bản thô cần lưu trữ.
            metadatas (Optional[List[Dict[str, Any]]]): Danh sách thông tin bổ sung đi kèm từng chunk
                (ví dụ: {"book_title": "Grammar in Use", "page_number": 10}).
            ids (Optional[List[str]]): Danh sách mã định danh duy nhất (Unique ID).
                Nếu là None, hệ thống sẽ tự động sinh mã ID ngẫu nhiên.

        Returns:
            List[str]: Danh sách các ID của tài liệu đã được lưu trữ thành công.
        """
        pass

    @abstractmethod
    def similarity_search(
        self,
        query: str,
        top_k: int = 3,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Tìm kiếm Top-k đoạn văn bản có độ tương đồng ngữ nghĩa cao nhất với câu hỏi.

        Args:
            query (str): Câu hỏi hoặc đoạn văn bản cần tìm kiếm.
            top_k (int): Số lượng kết quả liên quan nhất cần trả về. Mặc định là 3.
            where (Optional[Dict[str, Any]]): Bộ lọc điều kiện theo metadata
                (ví dụ: {"book_title": "English Grammar in Use"}).

        Returns:
            List[Dict[str, Any]]: Danh sách các kết quả tìm thấy, mỗi kết quả là một dict gồm:
                - "id": ID của chunk
                - "document": Nội dung văn bản gốc
                - "metadata": Thông tin nguồn gốc
                - "score" hoặc "distance": Điểm tương đồng hoặc khoảng cách Cosine.
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """Đếm tổng số lượng vector/chunk hiện đang được lưu trữ trong kho dữ liệu.

        Returns:
            int: Tổng số bản ghi.
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """Xóa toàn bộ dữ liệu trong bộ sưu tập (dùng khi kiểm thử hoặc tái nạp dữ liệu)."""
        pass
