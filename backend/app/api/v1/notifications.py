from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.notification import Notification
from app.schemas.notification import NotificationResponse, BroadcastCreate
from app.services.notifications import create_broadcast, send_shift_reminders
from app.services.audit import log_action

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/", response_model=list[NotificationResponse])
async def list_notifications(
    unread_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Notification).where(Notification.user_id == current_user.id)
    if unread_only:
        query = query.where(Notification.status == "pending")
    query = query.order_by(Notification.created_at.desc()).limit(100)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/unread-count")
async def unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(func.count()).select_from(Notification).where(
            Notification.user_id == current_user.id,
            Notification.status == "pending",
        )
    )
    return {"count": result.scalar()}


@router.patch("/{notif_id}/read")
async def mark_read(
    notif_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Notification).where(Notification.id == notif_id, Notification.user_id == current_user.id)
    )
    notif = result.scalar_one_or_none()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    notif.status = "sent"
    from sqlalchemy import func as sqlfunc
    notif.sent_at = sqlfunc.now()
    await db.commit()
    return {"message": "Marked as read"}


@router.patch("/read-all")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy import update
    await db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.status == "pending")
        .values(status="sent")
    )
    await db.commit()
    return {"message": "All marked as read"}


@router.post("/broadcast")
async def broadcast_message(
    data: BroadcastCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("coordinator", "controller"):
        raise HTTPException(status_code=403, detail="Coordinator or controller role required")

    count = await create_broadcast(
        db,
        tenant_id=current_user.tenant_id,
        sender_id=current_user.id,
        message=data.message,
        target=data.target,
        department_id=data.department_id,
        priority=data.priority,
    )

    await log_action(db, current_user.tenant_id, current_user.id, "broadcast", {
        "message": data.message[:200],
        "target": data.target,
        "department_id": data.department_id,
        "priority": data.priority,
        "recipients_count": count,
    })

    return {"message": f"Broadcast sent to {count} users"}


@router.post("/trigger-reminders")
async def trigger_reminders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("coordinator", "controller"):
        raise HTTPException(status_code=403, detail="Coordinator or controller role required")

    await send_shift_reminders(db)
    return {"message": "Reminders processed"}
