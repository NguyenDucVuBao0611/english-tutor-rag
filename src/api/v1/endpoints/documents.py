"""Endpoint quản lý và nạp tài liệu giáo trình vào Vector Database."""

import shutil
import tempfile
from pathlib import Path
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from src.api.dependencies import (
    get_chunker_service,
    get_document_service,
    get_vector_store,
)
from src.api.schemas.document import DocumentUploadResponse
from src.core.logger import logger
from src.services.chunker_service import ChunkerService
from src.services.document_service import DocumentMetadata, DocumentPage, DocumentService
from src.vector_store.chroma_store import ChromaVectorStore

router = APIRouter(prefix="/documents", tags=["Document Management"])


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tải lên và nạp tài liệu mới vào kho tri thức ChromaDB",
    description=(
        "Nhận file tài liệu (hỗ trợ .pdf, .txt), tự động làm sạch văn bản, "
        "phân đoạn đệ quy (Recursive Chunking kèm gối đầu Overlap), "
        "tạo vector embedding và lưu trữ vĩnh viễn vào ChromaDB."
    ),
)
async def upload_document(
    file: UploadFile = File(..., description="Tệp tài liệu cần nạp (PDF hoặc TXT)"),
    document_service: DocumentService = Depends(get_document_service),
    chunker_service: ChunkerService = Depends(get_chunker_service),
    vector_store: ChromaVectorStore = Depends(get_vector_store),
) -> DocumentUploadResponse:
    """Xử lý tải lên và lập chỉ mục tài liệu vào Vector Store."""
    filename = file.filename or "unknown_file"
    file_ext = Path(filename).suffix.lower()

    if file_ext not in [".pdf", ".txt"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Định dạng tệp '{file_ext}' không được hỗ trợ. Chỉ chấp nhận .pdf và .txt.",
        )

    logger.info(f"[API /upload] Bắt đầu xử lý tệp: '{filename}' (Định dạng: {file_ext})")

    # Tạo file tạm để xử lý
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
        temp_path = Path(tmp_file.name)
        shutil.copyfileobj(file.file, tmp_file)

    try:
        pages = []
        if file_ext == ".pdf":
            # Nạp và trích xuất PDF qua DocumentService
            pages = document_service.load_pdf(temp_path)
        elif file_ext == ".txt":
            # Đọc file văn bản thuần
            with open(temp_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            cleaned = document_service.clean_text(content)
            if cleaned:
                pages.append(
                    DocumentPage(
                        content=cleaned,
                        metadata=DocumentMetadata(
                            source=filename,
                            page_number=1,
                            total_pages=1,
                            char_count=len(cleaned),
                        ),
                    )
                )

        if not pages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tệp tin không chứa nội dung văn bản hợp lệ để xử lý.",
            )

        # Phân đoạn văn bản qua ChunkerService
        chunks = chunker_service.chunk_document_pages(pages)
        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể tạo các đoạn cắt (chunks) từ tài liệu.",
            )

        # Chuẩn bị dữ liệu nạp vào ChromaDB
        doc_contents = [c.content for c in chunks]
        doc_metadatas = [c.metadata.model_dump() for c in chunks]
        stem = Path(filename).stem
        doc_ids = [
            f"{stem}_p{c.metadata.page_number}_c{c.metadata.chunk_index}"
            for c in chunks
        ]

        # Lưu trữ vĩnh viễn vào Vector DB
        vector_store.add_documents(
            documents=doc_contents,
            metadatas=doc_metadatas,
            ids=doc_ids,
        )

        logger.info(
            f"[API /upload] Nạp thành công: {filename} ({len(pages)} trang, {len(chunks)} chunks)"
        )

        return DocumentUploadResponse(
            filename=filename,
            file_type=file_ext.replace(".", ""),
            total_pages=len(pages),
            total_chunks=len(chunks),
            message=f"Đã nạp thành công {len(chunks)} đoạn trích vào kho tri thức ChromaDB.",
            status="success",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API /upload] Lỗi xử lý tài liệu '{filename}': {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi máy chủ khi nạp tài liệu: {str(e)}",
        )
    finally:
        # Xóa file tạm
        if temp_path.exists():
            temp_path.unlink()
