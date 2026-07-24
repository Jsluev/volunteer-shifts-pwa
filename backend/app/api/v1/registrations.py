from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.shift import Shift
from app.models.registration import ShiftRegistration
from app.models.notification import Notification
from app.schemas.registration import RegistrationCreate, RegistrationUpdate, RegistrationResponse, BulkApprove
from app.services.audit import log_action
from app.services.notifications import create_notification

router = APIRouter(prefix="/registrations", tags=["registrations"])


@router.post("/", response_model=RegistrationResponse, status_code=201)
async def create_registration(
    data: RegistrationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Shift).where(Shift.id == data.shift_id, Shift.status == "published")
    )
    shift = result.scalar_one_or_none()
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found or not published")

    existing = await db.execute(
        select(ShiftRegistration).where(
            ShiftRegistration.shift_id == data.shift_id,
            ShiftRegistration.user_id == current_user.id,
            ShiftRegistration.status.in_(["pending", "approved", "attendance_confirmed"]),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already registered for this shift")

    occupied = await db.execute(
        select(func.count()).select_from(ShiftRegistration).where(
            ShiftRegistration.shift_id == data.shift_id,
            ShiftRegistration.status.in_(["approved", "attendance_confirmed"]),
        )
    )
    if occupied.scalar() >= shift.total_slots:
        raise HTTPException(status_code=400, detail="No available slots")

    auto_approve = True
    initial_status = "approved" if auto_approve else "pending"

    reg = ShiftRegistration(
        shift_id=data.shift_id,
        user_id=current_user.id,
        status=initial_status,
    )
    db.add(reg)
    await db.flush()

    if auto_approve:
        await create_notification(
            db,
            user_id=current_user.id,
            notif_type="registration",
            channel="inapp",
            subject="Вы записаны на смену",
            body=f"Вы записаны на смену #{shift.id}. Не забудьте подтвердить присутствие.",
        )
    else:
        await create_notification(
            db,
            user_id=current_user.id,
            notif_type="registration",
            channel="inapp",
            subject="Заявка на смену",
            body=f"Ваша заявка на смену #{shift.id} отправлена. Ожидайте подтверждения координатора.",
        )

    await db.commit()
    await db.refresh(reg)
    return reg


@router.get("/my", response_model=list[RegistrationResponse])
async def my_registrations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ShiftRegistration).where(
            ShiftRegistration.user_id == current_user.id,
            ShiftRegistration.status.in_(["pending", "approved", "attendance_confirmed"]),
        ).order_by(ShiftRegistration.created_at.desc())
    )
    return result.scalars().all()


@router.patch("/{reg_id}/cancel")
async def cancel_registration(
    reg_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(ShiftRegistration).where(ShiftRegistration.id == reg_id))
    reg = result.scalar_one_or_none()
    if not reg:
        raise HTTPException(status_code=404, detail="Registration not found")
    if reg.user_id != current_user.id and current_user.role not in ("coordinator", "controller"):
        raise HTTPException(status_code=403, detail="Not authorized")

    reg.status = "cancelled"

    if current_user.role in ("coordinator", "controller"):
        await log_action(db, current_user.tenant_id, current_user.id, "cancel_reg", {
            "registration_id": reg.id,
            "shift_id": reg.shift_id,
            "user_id": reg.user_id,
        })

    await db.commit()
    return {"message": "Registration cancelled"}


@router.patch("/{reg_id}/confirm-attendance")
async def confirm_attendance(
    reg_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(ShiftRegistration).where(ShiftRegistration.id == reg_id))
    reg = result.scalar_one_or_none()
    if not reg or reg.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Registration not found")
    if reg.status != "approved":
        raise HTTPException(status_code=400, detail="Can only confirm approved registrations")

    reg.status = "attendance_confirmed"
    await db.commit()
    return {"message": "Attendance confirmed"}


@router.patch("/{reg_id}/moderate")
async def moderate_registration(
    reg_id: int,
    data: RegistrationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("coordinator", "controller"):
        raise HTTPException(status_code=403, detail="Coordinator or controller role required")

    result = await db.execute(select(ShiftRegistration).where(ShiftRegistration.id == reg_id))
    reg = result.scalar_one_or_none()
    if not reg:
        raise HTTPException(status_code=404, detail="Registration not found")
    if data.status not in ("approved", "rejected", "cancelled"):
        raise HTTPException(status_code=400, detail="Invalid status")

    if data.status == "rejected" and not data.moderator_comment:
        raise HTTPException(status_code=400, detail="Comment required for rejection")

    if data.status == "approved":
        occupied = await db.execute(
            select(func.count()).select_from(ShiftRegistration).where(
                ShiftRegistration.shift_id == reg.shift_id,
                ShiftRegistration.status.in_(["approved", "attendance_confirmed"]),
            )
        )
        shift_result = await db.execute(select(Shift).where(Shift.id == reg.shift_id))
        shift = shift_result.scalar_one_or_none()
        if occupied.scalar() >= shift.total_slots:
            raise HTTPException(status_code=400, detail="No available slots")

    old_status = reg.status
    reg.status = data.status
    reg.moderator_comment = data.moderator_comment

    action = "approve_reg" if data.status == "approved" else "reject_reg" if data.status == "rejected" else "cancel_reg"
    await log_action(db, current_user.tenant_id, current_user.id, action, {
        "registration_id": reg.id,
        "shift_id": reg.shift_id,
        "user_id": reg.user_id,
        "old_status": old_status,
        "new_status": data.status,
        "comment": data.moderator_comment,
    })

    notif_body = f"Ваша заявка на смену #{reg.shift_id} {data.status == 'approved' and 'подтверждена' or 'отклонена'}."
    if data.moderator_comment:
        notif_body += f" Причина: {data.moderator_comment}"

    await create_notification(
        db,
        user_id=reg.user_id,
        notif_type="moderation",
        channel="inapp",
        subject="Решение по заявке",
        body=notif_body,
    )

    await db.commit()
    return {"message": f"Registration {data.status}"}


@router.post("/bulk-moderate")
async def bulk_moderate(
    data: BulkApprove,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("coordinator", "controller"):
        raise HTTPException(status_code=403, detail="Coordinator or controller role required")

    result = await db.execute(
        select(ShiftRegistration).where(ShiftRegistration.id.in_(data.registration_ids))
    )
    regs = result.scalars().all()

    new_status = "approved" if data.approve else "rejected"
    for reg in regs:
        reg.status = new_status

    await log_action(db, current_user.tenant_id, current_user.id, "bulk_moderate", {
        "registration_ids": data.registration_ids,
        "action": "approve" if data.approve else "reject",
        "count": len(regs),
    })

    await db.commit()
    return {"message": f"{len(regs)} registrations {new_status}"}
