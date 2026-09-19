import logging
import sys
from pathlib import Path

# Đường dẫn thư mục logs nằm ở thư mục gốc của dự án
BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "app.log"


def setup_logger(name: str = "RAG_TUTOR") -> logging.Logger:
    """Khởi tạo và cấu hình hệ thống ghi log chuẩn Enterprise.

    Hỗ trợ xuất log song song ra Console và lưu trữ lâu dài trong file.

    Args:
        name (str): Tên định danh của logger. Mặc định là 'RAG_TUTOR'.

    Returns:
        logging.Logger: Đối tượng logger đã được gắn các Handler và Formatter.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Tránh gắn lặp lại handler nếu hàm setup_logger được gọi nhiều lần
    if logger.handlers:
        return logger

    # Tự động tạo thư mục logs nếu chưa có
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Định dạng chuẩn: [Thời gian] [Mức độ] [File:Dòng] - Thông điệp
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 1. Console Handler: Xuất log ra màn hình terminal
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. File Handler: Lưu trữ log vào file logs/app.log (hỗ trợ tiếng Việt UTF-8)
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# Khởi tạo một instance dùng chung cho toàn bộ dự án (Singleton pattern)
logger = setup_logger()
