import os
from pathlib import Path
from dotenv import load_dotenv

# Tự động nạp file .env từ thư mục gốc
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

# Cấu hình API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Cấu hình Model AI
LLM_MODEL = "gemini-1.5-flash"
EMBEDDING_MODEL = "text-embedding-004"

# Đường dẫn thư mục dữ liệu & vector DB
DATA_DIR = ROOT_DIR / "data" / "raw"
CHROMA_DIR = ROOT_DIR / "chroma_data"
