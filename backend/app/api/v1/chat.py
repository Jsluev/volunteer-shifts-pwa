from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.dialog import Dialog
from app.models.message import ChatMessage
from app.schemas.chat import MessageCreate, MessageResponse, DialogCreate, DialogResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/dialogs", response_model=list[DialogResponse])
async def list_dialogs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Dialog).where(Dialog.tenant_id == current_user.tenant_id)
    )
    all_dialogs = result.scalars().all()
    return [
        d for d in all_dialogs
        if current_user.id in (d.participant_ids or [])
    ]


@router.post("/dialogs", response_model=DialogResponse, status_code=201)
async def create_dialog(
    data: DialogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    for pid in data.participant_ids:
        user = await db.execute(select(User).where(User.id == pid, User.tenant_id == current_user.tenant_id))
        if not user.scalar_one_or_none():
            raise HTTPException(status_code=404, detail=f"User {pid} not found")

    dialog = Dialog(
        tenant_id=current_user.tenant_id,
        type=data.type,
        participant_ids=data.participant_ids,
    )
    db.add(dialog)
    await db.commit()
    await db.refresh(dialog)
    return dialog


async def _check_dialog_access(db: AsyncSession, dialog_id: int, current_user: User) -> Dialog:
    result = await db.execute(select(Dialog).where(Dialog.id == dialog_id))
    dialog = result.scalar_one_or_none()
    if not dialog:
        raise HTTPException(status_code=404, detail="Dialog not found")
    if current_user.id not in (dialog.participant_ids or []):
        raise HTTPException(status_code=403, detail="Access denied")
    return dialog


@router.get("/dialogs/{dialog_id}/messages")
async def list_messages(
    dialog_id: int,
    limit: int = 50,
    before: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _check_dialog_access(db, dialog_id, current_user)

    query = select(ChatMessage).where(ChatMessage.dialog_id == dialog_id)
    if before:
        query = query.where(ChatMessage.id < before)
    query = query.order_by(ChatMessage.created_at.desc()).limit(limit)

    msgs = await db.execute(query)
    messages = msgs.scalars().all()
    messages.reverse()

    return [
        {
            "id": m.id,
            "dialog_id": m.dialog_id,
            "sender_id": m.sender_id,
            "text": m.text,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in messages
    ]


@router.post("/messages", response_model=MessageResponse, status_code=201)
async def send_message(
    data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _check_dialog_access(db, data.dialog_id, current_user)

    if not data.text.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    msg = ChatMessage(
        dialog_id=data.dialog_id,
        sender_id=current_user.id,
        text=data.text.strip(),
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg
