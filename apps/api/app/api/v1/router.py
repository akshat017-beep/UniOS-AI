from fastapi import APIRouter

from app.api.v1.routes import (
    admin,
    agents,
    auth,
    chat,
    coding,
    documents,
    health,
    multimodal,
    search,
    tools,
    university,
    users,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(tools.router, prefix="/tools", tags=["tools"])
api_router.include_router(coding.router, prefix="/coding", tags=["coding"])
api_router.include_router(multimodal.router, prefix="/multimodal", tags=["multimodal"])
api_router.include_router(university.router, prefix="/university", tags=["university"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
