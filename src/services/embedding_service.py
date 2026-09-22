import os
from typing import List, Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.core.logger import logger

# Tự động nạp API key từ .env
load_dotenv()


class EmbeddingService:
    """Service chịu trách nhiệm chuyển đổi văn bản thành Vector nhúng (Text Embedding).

    Áp dụng Singleton Pattern để duy trì 1 client duy nhất kết nối tới Google GenAI SDK.
    """

    _instance: Optional["EmbeddingService"] = None
    _client: Optional[genai.Client] = None

    def __new__(cls) -> "EmbeddingService":
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                error_msg = "Không tìm thấy GEMINI_API_KEY trong file .env!"
                logger.error(error_msg)
                raise ValueError(error_msg)

            cls._client = genai.Client(api_key=api_key)
            logger.info("Khởi tạo thành công Gemini Client Singleton cho EmbeddingService.")
        return cls._instance

    def __init__(self, model_name: str = "gemini-embedding-001"):
        self.model_name = model_name

    def embed_text(self, text: str) -> List[float]:
        """Tạo vector nhúng cho một đoạn văn bản đơn lẻ.

        Args:
            text (str): Đoạn văn bản cần vector hóa.

        Returns:
            List[float]: Vector số thực (thường là 3072 chiều) đại diện cho ngữ nghĩa của câu.
        """
        if not text or not text.strip():
            logger.warning("Đoạn text truyền vào rỗng, trả về vector 0.")
            return []

        try:
            response = self._client.models.embed_content(
                model=self.model_name,
                contents=text.strip(),
            )
            vector = response.embeddings[0].values
            return vector
        except Exception as e:
            logger.error(f"Lỗi khi gọi API tạo embedding: {str(e)}")
            raise

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Tạo vector nhúng cho một danh sách nhiều đoạn văn bản.

        Args:
            texts (List[str]): Danh sách các đoạn văn bản cần vector hóa.

        Returns:
            List[List[float]]: Danh sách các vector tương ứng.
        """
        if not texts:
            return []

        logger.info(f"Bắt đầu tạo embedding cho lô {len(texts)} văn bản...")
        vectors: List[List[float]] = []

        for idx, text in enumerate(texts):
            vec = self.embed_text(text)
            vectors.append(vec)

        logger.info(f"Hoàn thành tạo embedding cho {len(vectors)} văn bản.")
        return vectors
