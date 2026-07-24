from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.department import Department
from app.schemas.department import DepartmentCreate, DepartmentResponse

router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("/", response_model=list[DepartmentResponse])
async def list_departments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Department).where(Department.tenant_id == current_user.tenant_id)
    )
    return result.scalars().all()


@router.post("/", response_model=DepartmentResponse, status_code=201)
async def create_department(
    data: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("coordinator", "controller"):
        raise HTTPException(status_code=403, detail="Coordinator or controller role required")

    existing = await db.execute(
        select(Department).where(
            Department.tenant_id == current_user.tenant_id,
            Department.name == data.name,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Department already exists")

    dept = Department(tenant_id=current_user.tenant_id, name=data.name)
    db.add(dept)
    await db.commit()
    await db.refresh(dept)
    return dept


@router.delete("/{dept_id}")
async def delete_department(
    dept_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("coordinator", "controller"):
        raise HTTPException(status_code=403, detail="Coordinator or controller role required")

    result = await db.execute(
        select(Department).where(Department.id == dept_id, Department.tenant_id == current_user.tenant_id)
    )
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    await db.delete(dept)
    await db.commit()
    return {"message": "Department deleted"}
