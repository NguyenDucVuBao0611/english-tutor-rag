import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings

from src.config import CHROMA_DIR
from src.core.logger import logger
from src.services.embedding_service import EmbeddingService
from src.vector_store.base import BaseVectorStore


class ChromaVectorStore(BaseVectorStore):
    """Lớp triển khai cụ thể của BaseVectorStore sử dụng ChromaDB.
    
    Áp dụng Repository Pattern để quản lý việc lưu trữ bền vững (Persistence)
    và truy vấn tìm kiếm ngữ nghĩa (Semantic Search) cho các đoạn văn bản (chunks).
    """

    def __init__(
        self,
        collection_name: str = "english_tutor_collection",
        persist_directory: Optional[Path | str] = None,
        embedding_service: Optional[EmbeddingService] = None,
    ) -> None:
        """Khởi tạo ChromaVectorStore với cơ chế lưu trữ bền vững trên ổ cứng.

        Args:
            collection_name (str): Tên của bộ sưu tập (tương đương tên Bảng trong CSDL).
            persist_directory (Optional[Path | str]): Thư mục lưu dữ liệu SQLite và HNSW index.
                Nếu không truyền, mặc định lấy từ src.config.CHROMA_DIR.
            embedding_service (Optional[EmbeddingService]): Instance dịch vụ tạo vector (Dependency Injection).
                Nếu không truyền, sẽ tự khởi tạo EmbeddingService Singleton.
        """
        self.collection_name = collection_name
        self.persist_directory = Path(persist_directory or CHROMA_DIR)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        self.embedding_service = embedding_service or EmbeddingService()

        logger.info(
            f"Đang kết nối ChromaDB PersistentClient tại đường dẫn: '{self.persist_directory}'..."
        )
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False),
        )

        # Sử dụng không gian khoảng cách Cosine (hnsw:space = cosine)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            f"Khởi tạo thành công Collection '{self.collection_name}' (Hiện có: {self.count()} bản ghi)."
        )

    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """Tạo vector nhúng và lưu trữ danh sách các đoạn văn bản vào ChromaDB.

        Args:
            documents (List[str]): Danh sách các đoạn văn bản (chunks) cần thêm.
            metadatas (Optional[List[Dict[str, Any]]]): Metadata tương ứng với từng chunk.
            ids (Optional[List[str]]): Danh sách ID duy nhất. Nếu None, sẽ tự sinh UUID.

        Returns:
            List[str]: Danh sách ID đã được lưu trữ thành công.
        """
        if not documents:
            logger.warning("Danh sách documents truyền vào rỗng, bỏ qua thao tác add.")
            return []

        # Tự sinh ID nếu chưa có
        if ids is None:
            ids = [f"chunk_{uuid.uuid4().hex[:10]}" for _ in range(len(documents))]

        # Chuẩn hóa metadatas nếu chưa có
        if metadatas is None:
            metadatas = [{} for _ in range(len(documents))]

        logger.info(f"Đang tạo vector embedding cho {len(documents)} chunks...")
        embeddings = self.embedding_service.embed_batch(documents)

        logger.info(f"Đang lưu {len(documents)} bản ghi vào Collection '{self.collection_name}'...")
        try:
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )
            logger.info(f"Đã lưu thành công {len(documents)} chunks vào ChromaDB.")
            return ids
        except Exception as e:
            logger.error(f"Lỗi khi lưu dữ liệu vào ChromaDB: {str(e)}")
            raise

    def similarity_search(
        self,
        query: str,
        top_k: int = 3,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Tìm kiếm Top-k đoạn văn bản liên quan nhất bằng câu hỏi ngôn ngữ tự nhiên.

        Args:
            query (str): Câu hỏi của người học.
            top_k (int): Số lượng kết quả gần nhất cần lấy.
            where (Optional[Dict[str, Any]]): Bộ lọc metadata (vd: {"book_title": "Grammar in Use"}).

        Returns:
            List[Dict[str, Any]]: Danh sách các kết quả gồm: id, document, metadata, distance, score.
        """
        if not query or not query.strip():
            logger.warning("Câu hỏi truy vấn rỗng, trả về danh sách rỗng.")
            return []

        logger.info(f"Đang tạo vector cho câu hỏi truy vấn: '{query[:60]}...'")
        query_vector = self.embedding_service.embed_text(query)

        logger.info(f"Đang tìm kiếm Top-{top_k} trong ChromaDB (Lọc điều kiện: {where})...")
        try:
            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=top_k,
                where=where,
                include=["documents", "metadatas", "distances"],
            )

            formatted_results: List[Dict[str, Any]] = []
            if results and results.get("ids") and len(results["ids"]) > 0:
                ids_list = results["ids"][0]
                docs_list = results.get("documents", [[]])[0]
                meta_list = results.get("metadatas", [[]])[0]
                dist_list = results.get("distances", [[]])[0]

                for idx in range(len(ids_list)):
                    dist = dist_list[idx] if idx < len(dist_list) else 0.0
                    # Trong không gian Cosine của ChromaDB:
                    # Cosine Distance = 1 - Cosine Similarity
                    # => Similarity Score = 1 - Distance
                    score = max(0.0, 1.0 - dist)

                    formatted_results.append(
                        {
                            "id": ids_list[idx],
                            "document": docs_list[idx] if idx < len(docs_list) else "",
                            "metadata": meta_list[idx] if idx < len(meta_list) else {},
                            "distance": round(dist, 4),
                            "score": round(score, 4),
                        }
                    )

            logger.info(f"Tìm thấy {len(formatted_results)} kết quả tương đồng phù hợp.")
            return formatted_results

        except Exception as e:
            logger.error(f"Lỗi khi truy vấn dữ liệu từ ChromaDB: {str(e)}")
            raise

    def count(self) -> int:
        """Đếm tổng số lượng bản ghi trong collection hiện tại."""
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"Lỗi khi đếm số bản ghi trong ChromaDB: {str(e)}")
            return 0

    def reset(self) -> None:
        """Xóa sạch toàn bộ dữ liệu trong collection hiện tại."""
        logger.warning(f"Đang xóa toàn bộ dữ liệu trong Collection '{self.collection_name}'...")
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(f"Đã reset thành công Collection '{self.collection_name}'.")
        except Exception as e:
            logger.error(f"Lỗi khi reset Collection: {str(e)}")
            raise
