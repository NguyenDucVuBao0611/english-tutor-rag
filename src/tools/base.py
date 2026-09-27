from abc import ABC, abstractmethod
from typing import Any, Dict
from pydantic import BaseModel


class BaseTool(ABC):
    """Interface cơ sở chuẩn hóa cho mọi Công cụ (Tool) mà AI Agent có thể sử dụng.
    
    Tuân thủ nguyên tắc Single Responsibility và Open/Closed Principle.
    Mỗi tool bắt buộc phải có:
    - name: Tên duy nhất của công cụ để LLM gọi.
    - description: Mô tả rõ ràng chức năng và ngữ cảnh sử dụng để LLM tự quyết định kích hoạt.
    - args_schema: Lớp Pydantic định nghĩa kiểu dữ liệu và mô tả các tham số đầu vào.
    """

    name: str
    description: str
    args_schema: type[BaseModel]

    @abstractmethod
    def execute(self, **kwargs: Any) -> Any:
        """Thực thi logic nghiệp vụ của công cụ.

        Args:
            **kwargs: Các tham số truyền vào khớp với args_schema.

        Returns:
            Any: Kết quả trả về (thường là chuỗi văn bản hoặc dict có cấu trúc) để Agent quan sát.
        """
        pass

    def to_schema(self) -> Dict[str, Any]:
        """Xuất thông số kỹ thuật của Tool thành cấu trúc Schema chuẩn cho LLM."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.args_schema.model_json_schema(),
        }
