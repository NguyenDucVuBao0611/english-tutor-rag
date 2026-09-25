import os
from typing import Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.core.logger import logger

# Nạp biến môi trường từ .env
load_dotenv()


class LLMService:
    """Service quản lý việc tương tác với các Mô hình Ngôn ngữ Lớn (LLM) của Google GenAI.

    Áp dụng Singleton Pattern để duy trì 1 client kết nối duy nhất,
    giúp tối ưu hóa tài nguyên mạng và tốc độ phản hồi.
    """

    _instance: Optional["LLMService"] = None
    _client: Optional[genai.Client] = None

    def __new__(cls) -> "LLMService":
        if cls._instance is None:
            cls._instance = super(LLMService, cls).__new__(cls)
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                error_msg = "Không tìm thấy GEMINI_API_KEY trong file .env!"
                logger.error(error_msg)
                raise ValueError(error_msg)

            cls._client = genai.Client(api_key=api_key)
            logger.info("Khởi tạo thành công Gemini Client Singleton cho LLMService.")
        return cls._instance

    def __init__(self, model_name: Optional[str] = None) -> None:
        """Khởi tạo cấu hình cho LLMService.

        Args:
            model_name (Optional[str]): Tên model Gemini muốn sử dụng.
                Mặc định lấy từ biến môi trường LLM_MODEL hoặc dùng 'gemini-3.8-flash'.
        """
        self.model_name = model_name or os.getenv("LLM_MODEL", "gemini-3.8-flash")

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
    ) -> str:
        """Sinh câu trả lời từ LLM với cấu hình nhiệt độ (temperature) và chỉ thị hệ thống.

        Args:
            prompt (str): Nội dung câu hỏi / yêu cầu từ người dùng.
            system_instruction (Optional[str]): Hướng dẫn định hình phong cách và nguyên tắc cho AI.
            temperature (float): Mức độ ngẫu hứng (0.0 - 1.0). Mặc định 0.2 để giảm thiểu ảo giác.

        Returns:
            str: Nội dung câu trả lời từ mô hình.
        """
        if not prompt or not prompt.strip():
            logger.warning("Prompt gửi tới LLM rỗng, trả về chuỗi rỗng.")
            return ""

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
        )

        logger.info(f"Đang gửi prompt tới Gemini LLM (Model: '{self.model_name}', Temp: {temperature})...")

        try:
            response = self._client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config,
            )
            return response.text or ""
        except Exception as e:
            # Cơ chế fallback dự phòng
            logger.warning(f"Lỗi khi gọi model '{self.model_name}': {str(e)}. Thử fallback sang 'gemini-3.6-flash'...")
            try:
                fallback_response = self._client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=prompt,
                    config=config,
                )
                return fallback_response.text or ""
            except Exception as fallback_err:
                logger.error(f"Lỗi nghiêm trọng khi gọi LLM fallback: {str(fallback_err)}")
                raise
