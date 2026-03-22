"""API package for thin route handlers and request/response contracts."""

from fastapi import APIRouter

from app.api.routes import router as health_router

api_router = APIRouter()
api_router.include_router(health_router)
