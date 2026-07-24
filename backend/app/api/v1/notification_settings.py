from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.notification_settings import NotificationSettings

router = APIRouter(prefix="/notification-settings", tags=["notification-settings"])


@router.get("/", response_model=NotificationSettings)
async def get_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one_or_none()
    settings = user.settings if hasattr(user, 'settings') and user.settings else {}
    return NotificationSettings(**settings)


@router.put("/", response_model=NotificationSettings)
async def update_settings(
    data: NotificationSettings,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.settings = data.model_dump()
    await db.commit()
    return data
