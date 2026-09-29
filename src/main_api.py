"""Điểm khởi chạy chính của hệ thống FastAPI Backend (Enterprise AI English Tutor)."""

import sys
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Đảm bảo đường dẫn gốc của dự án nằm trong sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.api.dependencies import get_tutor_agent, get_vector_store
from src.api.v1.endpoints.health import router as health_router
from src.api.v1.router import api_v1_router
from src.core.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Quản lý vòng đời khởi động và tắt an toàn của FastAPI App."""
    logger.info("====================================================================")
    logger.info("🚀 KHỞI ĐỘNG FASTAPI BACKEND SERVER - ENTERPRISE AI ENGLISH TUTOR")
    logger.info("====================================================================")

    # Làm nóng (Warm-up) sẵn sàng tài nguyên nặng vào RAM
    try:
        logger.info("[Lifespan] Đang làm nóng Vector Store và nạp TutorAgent vào RAM...")
        store = get_vector_store()
        agent = get_tutor_agent()
        logger.info(f"[Lifespan] Khởi tạo thành công! Tổng số documents: {store.count()}")
    except Exception as e:
        logger.error(f"[Lifespan] Cảnh báo khi làm nóng tài nguyên: {e}")

    yield

    logger.info("====================================================================")
    logger.info("🛑 ĐANG TẮT FASTAPI BACKEND SERVER VÀ GIẢI PHÓNG TÀI NGUYÊN...")
    logger.info("====================================================================")


# Khởi tạo ứng dụng FastAPI với đầy đủ Metadata chuẩn OpenAPI
app = FastAPI(
    title="🎓 Enterprise AI English Tutor API",
    description=(
        "Hệ thống Backend RESTful API chuẩn Enterprise cho Gia Sư Tiếng Anh Tự Trị.\n\n"
        "### 🌟 Các Tính Năng Cốt Lõi:\n"
        "- **Autonomous ReAct Agent**: Tự chủ suy luận, phân loại ý định (Intent Routing), "
        "kích hoạt công cụ và trích dẫn giáo trình chính xác.\n"
        "- **RAG Triad Knowledge Engine**: ChromaDB Vector Store lưu trữ vĩnh viễn và tìm kiếm ngữ nghĩa theo Cosine Similarity.\n"
        "- **Document Pipeline**: Tải lên PDF/TXT, tự động băm nhỏ đệ quy và đánh chỉ mục.\n"
        "- **Type-Safe DTOs**: 100% Pydantic V2 Validation & Tự động sinh tài liệu Swagger UI."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Cấu hình CORS Middleware mở cổng cho Web UI (Streamlit / React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong môi trường dev mở tự do cho Web Streamlit (Port 8501)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký Health Router ở gốc để các công cụ cân bằng tải (Load Balancer/Docker) dễ kiểm tra
app.include_router(health_router)

# Đăng ký toàn bộ Router v1
app.include_router(api_v1_router, prefix="/api/v1")


@app.get(
    "/",
    status_code=status.HTTP_200_OK,
    summary="Cổng chào mừng API",
    tags=["Root"],
)
async def root_welcome():
    """Thông tin chào mừng và điều hướng nhanh đến tài liệu Swagger."""
    return JSONResponse(
        content={
            "app_name": "Enterprise AI English Tutor API",
            "version": "1.0.0",
            "status": "online",
            "documentation": {
                "swagger_ui": "/docs",
                "redoc": "/redoc",
                "openapi_spec": "/openapi.json",
            },
            "endpoints": {
                "health": "/health",
                "agent_chat": "/api/v1/agent/chat",
                "document_upload": "/api/v1/documents/upload",
            },
        }
    )


if __name__ == "__main__":
    import uvicorn

    logger.info("Chạy server qua Uvicorn tại http://127.0.0.1:8000 ...")
    uvicorn.run("src.main_api:app", host="127.0.0.1", port=8000, reload=True)
