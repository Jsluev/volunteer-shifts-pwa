import csv
import io
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, extract
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.shift import Shift
from app.models.registration import ShiftRegistration
from app.models.audit import AuditLog

router = APIRouter(prefix="/analytics", tags=["analytics"])


def require_coordinator(user: User):
    if user.role not in ("coordinator", "controller"):
        raise HTTPException(status_code=403, detail="Coordinator or controller role required")


@router.get("/fill-rate")
async def fill_rate(
    start_date: str | None = None,
    end_date: str | None = None,
    department_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_coordinator(current_user)

    query = select(Shift).where(Shift.tenant_id == current_user.tenant_id, Shift.status == "published")
    if start_date:
        query = query.where(Shift.start_time >= start_date)
    if end_date:
        query = query.where(Shift.end_time <= end_date)
    if department_id:
        query = query.where(Shift.department_id == department_id)

    result = await db.execute(query)
    shifts = result.scalars().all()

    total_slots = 0
    filled_slots = 0
    for shift in shifts:
        total_slots += shift.total_slots
        occupied = await db.execute(
            select(func.count()).select_from(ShiftRegistration).where(
                ShiftRegistration.shift_id == shift.id,
                ShiftRegistration.status.in_(["approved", "attendance_confirmed"]),
            )
        )
        filled_slots += occupied.scalar()

    rate = (filled_slots / total_slots * 100) if total_slots > 0 else 0
    return {
        "total_shifts": len(shifts),
        "total_slots": total_slots,
        "filled_slots": filled_slots,
        "fill_rate_percent": round(rate, 1),
        "empty_slots": total_slots - filled_slots,
    }


@router.get("/volunteer-stats/{user_id}")
async def volunteer_stats(
    user_id: int,
    month: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_coordinator(current_user)

    query = select(ShiftRegistration).where(ShiftRegistration.user_id == user_id)
    if month:
        start = datetime.strptime(month, "%Y-%m")
        end = start + timedelta(days=32)
        end = end.replace(day=1)
        query = query.where(
            ShiftRegistration.created_at >= start,
            ShiftRegistration.created_at < end,
        )

    result = await db.execute(query)
    regs = result.scalars().all()

    total = len(regs)
    approved = sum(1 for r in regs if r.status in ("approved",))
    confirmed = sum(1 for r in regs if r.status == "attendance_confirmed")
    cancelled = sum(1 for r in regs if r.status == "cancelled")
    rejected = sum(1 for r in regs if r.status == "rejected")

    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()

    return {
        "user_id": user_id,
        "user_name": user.full_name if user else None,
        "user_email": user.email if user else None,
        "total_registrations": total,
        "approved": approved,
        "attendance_confirmed": confirmed,
        "cancelled": cancelled,
        "rejected": rejected,
        "attendance_rate": round(confirmed / approved * 100, 1) if approved > 0 else 0,
    }


@router.get("/volunteer-classification")
async def volunteer_classification(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_coordinator(current_user)

    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    volunteers = await db.execute(
        select(User).where(User.tenant_id == current_user.tenant_id, User.role == "volunteer", User.is_active == True)
    )

    classifications = {
        "active_3plus": [],
        "active_1_2": [],
        "inactive_registered": [],
        "never_came": [],
    }

    for vol in volunteers.scalars().all():
        month_regs = await db.execute(
            select(func.count()).select_from(ShiftRegistration).where(
                ShiftRegistration.user_id == vol.id,
                ShiftRegistration.status.in_(["approved", "attendance_confirmed"]),
                ShiftRegistration.created_at >= month_start,
            )
        )
        count = month_regs.scalar()

        total_regs = await db.execute(
            select(func.count()).select_from(ShiftRegistration).where(
                ShiftRegistration.user_id == vol.id,
            )
        )
        total = total_regs.scalar()

        vol_info = {"id": vol.id, "name": vol.full_name, "email": vol.email, "shifts_this_month": count}

        if count >= 3:
            classifications["active_3plus"].append(vol_info)
        elif count >= 1:
            classifications["active_1_2"].append(vol_info)
        elif total > 0:
            classifications["inactive_registered"].append(vol_info)
        else:
            classifications["never_came"].append(vol_info)

    return {
        "month": month_start.strftime("%Y-%m"),
        "total_volunteers": sum(len(v) for v in classifications.values()),
        "classifications": {
            k: {"count": len(v), "volunteers": v}
            for k, v in classifications.items()
        },
    }


@router.get("/unfilled-slots")
async def unfilled_slots(
    department_id: int | None = None,
    days_ahead: int = 7,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_coordinator(current_user)

    now = datetime.utcnow()
    future = now + timedelta(days=days_ahead)

    query = select(Shift).where(
        Shift.tenant_id == current_user.tenant_id,
        Shift.status == "published",
        Shift.start_time >= now,
        Shift.start_time <= future,
    )
    if department_id:
        query = query.where(Shift.department_id == department_id)

    result = await db.execute(query)
    shifts = result.scalars().all()

    unfilled = []
    for shift in shifts:
        occupied = await db.execute(
            select(func.count()).select_from(ShiftRegistration).where(
                ShiftRegistration.shift_id == shift.id,
                ShiftRegistration.status.in_(["approved", "attendance_confirmed"]),
            )
        )
        occ = occupied.scalar()
        if occ < shift.total_slots:
            unfilled.append({
                "shift_id": shift.id,
                "department_id": shift.department_id,
                "start_time": shift.start_time.isoformat(),
                "end_time": shift.end_time.isoformat(),
                "total_slots": shift.total_slots,
                "occupied": occ,
                "empty": shift.total_slots - occ,
            })

    return {"shifts": unfilled, "total_unfilled": len(unfilled)}


@router.get("/audit")
async def audit_log(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    action_type: str | None = None,
    user_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_coordinator(current_user)

    query = select(AuditLog).where(AuditLog.tenant_id == current_user.tenant_id)
    if action_type:
        query = query.where(AuditLog.action_type == action_type)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)

    count_query = select(func.count()).select_from(AuditLog).where(AuditLog.tenant_id == current_user.tenant_id)
    if action_type:
        count_query = count_query.where(AuditLog.action_type == action_type)
    if user_id:
        count_query = count_query.where(AuditLog.user_id == user_id)

    total = await db.execute(count_query)

    offset = (page - 1) * page_size
    query = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "logs": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action_type": log.action_type,
                "meta": log.meta,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
        "total": total.scalar(),
        "page": page,
        "page_size": page_size,
    }


@router.get("/export/fill-rate")
async def export_fill_rate_csv(
    start_date: str | None = None,
    end_date: str | None = None,
    department_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_coordinator(current_user)

    query = select(Shift).where(Shift.tenant_id == current_user.tenant_id, Shift.status == "published")
    if start_date:
        query = query.where(Shift.start_time >= start_date)
    if end_date:
        query = query.where(Shift.end_time <= end_date)
    if department_id:
        query = query.where(Shift.department_id == department_id)

    result = await db.execute(query)
    shifts = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Shift ID", "Department", "Start", "End", "Total Slots", "Filled", "Empty", "Fill Rate %"])

    for shift in shifts:
        occupied = await db.execute(
            select(func.count()).select_from(ShiftRegistration).where(
                ShiftRegistration.shift_id == shift.id,
                ShiftRegistration.status.in_(["approved", "attendance_confirmed"]),
            )
        )
        occ = occupied.scalar()
        rate = round(occ / shift.total_slots * 100, 1) if shift.total_slots > 0 else 0
        writer.writerow([
            shift.id, shift.department_id,
            shift.start_time.isoformat(), shift.end_time.isoformat(),
            shift.total_slots, occ, shift.total_slots - occ, rate,
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=fill_rate_{datetime.utcnow().strftime('%Y%m%d')}.csv"},
    )


@router.get("/export/unfilled-slots")
async def export_unfilled_csv(
    department_id: int | None = None,
    days_ahead: int = 7,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_coordinator(current_user)

    now = datetime.utcnow()
    future = now + timedelta(days=days_ahead)

    query = select(Shift).where(
        Shift.tenant_id == current_user.tenant_id,
        Shift.status == "published",
        Shift.start_time >= now,
        Shift.start_time <= future,
    )
    if department_id:
        query = query.where(Shift.department_id == department_id)

    result = await db.execute(query)
    shifts = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Shift ID", "Department", "Start", "End", "Total", "Occupied", "Empty"])

    for shift in shifts:
        occupied = await db.execute(
            select(func.count()).select_from(ShiftRegistration).where(
                ShiftRegistration.shift_id == shift.id,
                ShiftRegistration.status.in_(["approved", "attendance_confirmed"]),
            )
        )
        occ = occupied.scalar()
        if occ < shift.total_slots:
            writer.writerow([
                shift.id, shift.department_id,
                shift.start_time.isoformat(), shift.end_time.isoformat(),
                shift.total_slots, occ, shift.total_slots - occ,
            ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=unfilled_slots_{datetime.utcnow().strftime('%Y%m%d')}.csv"},
    )


@router.get("/export/volunteer-classification")
async def export_classification_csv(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_coordinator(current_user)

    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    volunteers = await db.execute(
        select(User).where(User.tenant_id == current_user.tenant_id, User.role == "volunteer", User.is_active == True)
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["User ID", "Name", "Email", "Shifts This Month", "Classification"])

    for vol in volunteers.scalars().all():
        month_regs = await db.execute(
            select(func.count()).select_from(ShiftRegistration).where(
                ShiftRegistration.user_id == vol.id,
                ShiftRegistration.status.in_(["approved", "attendance_confirmed"]),
                ShiftRegistration.created_at >= month_start,
            )
        )
        count = month_regs.scalar()

        if count >= 3:
            tier = "Active (3+)"
        elif count >= 1:
            tier = "Moderate (1-2)"
        else:
            total_regs = await db.execute(
                select(func.count()).select_from(ShiftRegistration).where(ShiftRegistration.user_id == vol.id)
            )
            tier = "Registered" if total_regs.scalar() > 0 else "Never came"

        writer.writerow([vol.id, vol.full_name, vol.email, count, tier])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=classification_{datetime.utcnow().strftime('%Y%m%d')}.csv"},
    )
