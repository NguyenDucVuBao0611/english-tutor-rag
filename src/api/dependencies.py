"""Dependency Injection Container cho FastAPI.

Cung cấp các đối tượng Singleton (ChromaVectorStore, RAGService, TutorAgent...)
để tránh khởi tạo lại nhiều lần gây tốn tài nguyên RAM và CPU.
"""

from typing import Optional
from fastapi import Depends

from src.core.logger import logger
from src.agents.tutor_agent import TutorAgent
from src.services.chunker_service import ChunkerService
from src.services.document_service import DocumentService
from src.services.rag_service import RAGService
from src.tools.rag_tool import GrammarRetrievalTool
from src.vector_store.chroma_store import ChromaVectorStore

# Khởi tạo các biến lưu trữ Singleton trong bộ nhớ
_vector_store: Optional[ChromaVectorStore] = None
_rag_service: Optional[RAGService] = None
_grammar_tool: Optional[GrammarRetrievalTool] = None
_tutor_agent: Optional[TutorAgent] = None
_document_service: Optional[DocumentService] = None
_chunker_service: Optional[ChunkerService] = None


def get_vector_store() -> ChromaVectorStore:
    """Dependency cung cấp thể hiện Singleton của ChromaVectorStore."""
    global _vector_store
    if _vector_store is None:
        logger.info("[Dependency Injection] Khởi tạo thể hiện Singleton của ChromaVectorStore...")
        _vector_store = ChromaVectorStore()
    return _vector_store


def get_rag_service(vector_store: ChromaVectorStore = Depends(get_vector_store)) -> RAGService:
    """Dependency cung cấp thể hiện Singleton của RAGService."""
    global _rag_service
    if _rag_service is None or _rag_service.vector_store is not vector_store:
        logger.info("[Dependency Injection] Khởi tạo thể hiện RAGService gắn với VectorStore hiện tại...")
        _rag_service = RAGService(vector_store=vector_store)
    return _rag_service


def get_grammar_tool(rag_service: RAGService = Depends(get_rag_service)) -> GrammarRetrievalTool:
    """Dependency cung cấp thể hiện Singleton của GrammarRetrievalTool."""
    global _grammar_tool
    if _grammar_tool is None or _grammar_tool.rag_service is not rag_service:
        logger.info("[Dependency Injection] Khởi tạo thể hiện GrammarRetrievalTool...")
        _grammar_tool = GrammarRetrievalTool(rag_service=rag_service)
    return _grammar_tool


def get_tutor_agent(grammar_tool: GrammarRetrievalTool = Depends(get_grammar_tool)) -> TutorAgent:
    """Dependency cung cấp thể hiện Singleton của TutorAgent (ReAct Engine)."""
    global _tutor_agent
    if _tutor_agent is None or (len(_tutor_agent.tools) > 0 and _tutor_agent.tools[0] is not grammar_tool):
        logger.info("[Dependency Injection] Khởi tạo thể hiện TutorAgent gắn với Tool hiện tại...")
        _tutor_agent = TutorAgent(tools=[grammar_tool])
    return _tutor_agent


def get_document_service() -> DocumentService:
    """Dependency cung cấp DocumentService nạp và làm sạch PDF."""
    global _document_service
    if _document_service is None:
        logger.info("[Dependency Injection] Khởi tạo DocumentService...")
        _document_service = DocumentService()
    return _document_service


def get_chunker_service() -> ChunkerService:
    """Dependency cung cấp ChunkerService chia nhỏ tài liệu."""
    global _chunker_service
    if _chunker_service is None:
        logger.info("[Dependency Injection] Khởi tạo ChunkerService...")
        _chunker_service = ChunkerService()
    return _chunker_service


def reset_dependencies() -> None:
    """Hàm hỗ trợ kiểm thử: Reset toàn bộ Singleton cache."""
    global _vector_store, _rag_service, _grammar_tool, _tutor_agent, _document_service, _chunker_service
    _vector_store = None
    _rag_service = None
    _grammar_tool = None
    _tutor_agent = None
    _document_service = None
    _chunker_service = None
    logger.info("[Dependency Injection] Đã dọn sạch toàn bộ Singleton cache.")
