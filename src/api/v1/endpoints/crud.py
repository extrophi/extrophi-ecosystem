from fastapi import APIRouter, Depends
from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.core.security import get_current_user

router = APIRouter()


@router.post("/{model_name}")
async def create_item(
    model_name: str,
    data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    return {"id": "new_item_id", "model": model_name, "data": data}