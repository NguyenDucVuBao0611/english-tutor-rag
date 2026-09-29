"""Tổng hợp các APIRouter cho phiên bản v1."""

from fastapi import APIRouter

from src.api.v1.endpoints.agent import router as agent_router
from src.api.v1.endpoints.documents import router as documents_router
from src.api.v1.endpoints.health import router as health_router

api_v1_router = APIRouter()

# Tích hợp các router thành phần
api_v1_router.include_router(health_router)
api_v1_router.include_router(agent_router)
api_v1_router.include_router(documents_router)
