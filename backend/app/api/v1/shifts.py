from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.shift import Shift
from app.models.registration import ShiftRegistration
from app.models.department import Department
from app.schemas.shift import ShiftCreate, ShiftUpdate, ShiftResponse
from app.services.audit import log_action

router = APIRouter(prefix="/shifts", tags=["shifts"])


def require_coordinator(user: User):
    if user.role not in ("coordinator", "controller", "admin"):
        raise HTTPException(status_code=403, detail="Coordinator or controller role required")


@router.get("/", response_model=list[ShiftResponse])
async def list_shifts(
    department_id: int | None = None,
    status: str = "published",
    start_date: str | None = None,
    end_date: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Shift).where(Shift.tenant_id == current_user.tenant_id)
    if status:
        query = query.where(Shift.status == status)
    if department_id:
        query = query.where(Shift.department_id == department_id)
    if start_date:
        query = query.where(Shift.start_time >= start_date)
    if end_date:
        query = query.where(Shift.end_time <= end_date)
    query = query.order_by(Shift.start_time)

    result = await db.execute(query)
    shifts = result.scalars().all()

    response = []
    for shift in shifts:
        occupied = await db.execute(
            select(func.count()).select_from(ShiftRegistration).where(
                ShiftRegistration.shift_id == shift.id,
                ShiftRegistration.status.in_(["approved", "attendance_confirmed"]),
            )
        )
        shift_dict = ShiftResponse.model_validate(shift)
        shift_dict.occupied_slots = occupied.scalar()
        response.append(shift_dict)
    return response


@router.post("/", response_model=ShiftResponse, status_code=201)
async def create_shift(
    data: ShiftCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_coordinator(current_user)

    dept = await db.execute(
        select(Department).where(Department.id == data.department_id, Department.tenant_id == current_user.tenant_id)
    )
    if not dept.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Department not found")

    if data.end_time <= data.start_time:
        raise HTTPException(status_code=400, detail="End time must be after start time")

    shift = Shift(
        tenant_id=current_user.tenant_id,
        department_id=data.department_id,
        start_time=data.start_time,
        end_time=data.end_time,
        total_slots=data.total_slots,
        status="draft",
        created_by=current_user.id,
    )
    db.add(shift)
    await db.flush()

    await log_action(db, current_user.tenant_id, current_user.id, "create_shift", {
        "shift_id": shift.id,
        "department_id": data.department_id,
        "start_time": data.start_time.isoformat(),
        "total_slots": data.total_slots,
    })
    await db.commit()
    await db.refresh(shift)
    return shift


@router.put("/{shift_id}", response_model=ShiftResponse)
async def update_shift(
    shift_id: int,
    data: ShiftUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_coordinator(current_user)
    result = await db.execute(
        select(Shift).where(Shift.id == shift_id, Shift.tenant_id == current_user.tenant_id)
    )
    shift = result.scalar_one_or_none()
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")

    if data.total_slots is not None and data.total_slots != shift.total_slots:
        occupied = await db.execute(
            select(func.count()).select_from(ShiftRegistration).where(
                ShiftRegistration.shift_id == shift.id,
                ShiftRegistration.status.in_(["approved", "attendance_confirmed"]),
            )
        )
        if data.total_slots < occupied.scalar():
            raise HTTPException(
                status_code=400,
                detail=f"Cannot reduce slots below current occupied count ({occupied.scalar()})"
            )

    changes = {}
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        old_val = getattr(shift, field)
        if old_val != value:
            changes[field] = {"old": str(old_val), "new": str(value)}
            setattr(shift, field, value)

    if changes:
        await log_action(db, current_user.tenant_id, current_user.id, "change_shift", {
            "shift_id": shift.id,
            "changes": changes,
        })

    await db.commit()
    await db.refresh(shift)
    return shift


@router.patch("/{shift_id}/publish")
async def publish_shift(
    shift_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_coordinator(current_user)
    result = await db.execute(
        select(Shift).where(Shift.id == shift_id, Shift.tenant_id == current_user.tenant_id)
    )
    shift = result.scalar_one_or_none()
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")
    if shift.status != "draft":
        raise HTTPException(status_code=400, detail="Only draft shifts can be published")

    shift.status = "published"
    await log_action(db, current_user.tenant_id, current_user.id, "publish_shift", {"shift_id": shift.id})
    await db.commit()
    return {"message": "Shift published"}


@router.patch("/{shift_id}/cancel")
async def cancel_shift(
    shift_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_coordinator(current_user)
    result = await db.execute(
        select(Shift).where(Shift.id == shift_id, Shift.tenant_id == current_user.tenant_id)
    )
    shift = result.scalar_one_or_none()
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")

    regs = await db.execute(
        select(ShiftRegistration).where(
            ShiftRegistration.shift_id == shift_id,
            ShiftRegistration.status.in_(["approved", "pending"]),
        )
    )
    for reg in regs.scalars().all():
        reg.status = "cancelled"

    shift.status = "cancelled"
    await log_action(db, current_user.tenant_id, current_user.id, "cancel_shift", {"shift_id": shift.id})
    await db.commit()
    return {"message": "Shift cancelled"}


@router.delete("/{shift_id}")
async def delete_shift(
    shift_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_coordinator(current_user)
    result = await db.execute(
        select(Shift).where(Shift.id == shift_id, Shift.tenant_id == current_user.tenant_id)
    )
    shift = result.scalar_one_or_none()
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")

    await log_action(db, current_user.tenant_id, current_user.id, "delete_shift", {"shift_id": shift.id})
    await db.delete(shift)
    await db.commit()
    return {"message": "Shift deleted"}


@router.get("/{shift_id}/registrations")
async def list_shift_registrations(
    shift_id: int,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_coordinator(current_user)

    query = select(ShiftRegistration).where(ShiftRegistration.shift_id == shift_id)
    if status:
        query = query.where(ShiftRegistration.status == status)
    query = query.order_by(ShiftRegistration.created_at)

    result = await db.execute(query)
    regs = result.scalars().all()

    response = []
    for reg in regs:
        user = await db.execute(select(User).where(User.id == reg.user_id))
        user_obj = user.scalar_one_or_none()
        response.append({
            "id": reg.id,
            "shift_id": reg.shift_id,
            "user_id": reg.user_id,
            "user_name": user_obj.full_name if user_obj else None,
            "user_email": user_obj.email if user_obj else None,
            "status": reg.status,
            "moderator_comment": reg.moderator_comment,
            "created_at": reg.created_at.isoformat() if reg.created_at else None,
        })
    return response
