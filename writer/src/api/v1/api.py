from fastapi import APIRouter

from src.api.v1.endpoints import auth, users, crud, vector, websocket

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(crud.router, prefix="/crud", tags=["crud"])
api_router.include_router(vector.router, prefix="/vector", tags=["vector"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])