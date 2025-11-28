from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from core.database import get_db
from models.user import User
from schemas.schemas import UserSearchResponse
from api.deps import get_current_user

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/search", response_model=List[UserSearchResponse])
async def search_users(
    q: str = Query(..., min_length=3, description="Search term (username)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Search users by username."""
    result = await db.execute(
        select(User)
        .where(User.username.ilike(f"%{q}%"))
        .limit(10)
    )
    users = result.scalars().all()
    return users
