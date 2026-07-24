from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from app.api.v1 import auth, shifts, registrations, departments, notifications, chat, analytics
from app.api.v1 import notification_settings
from app.models import Tenant, User, Department, Shift, ShiftRegistration, Dialog, ChatMessage, Notification, AuditLog
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password

app = FastAPI(
    title="Volunteer Shifts API",
    description="System for managing volunteer shifts in hospitals",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(departments.router, prefix="/api/v1")
app.include_router(shifts.router, prefix="/api/v1")
app.include_router(registrations.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(notification_settings.router, prefix="/api/v1")


@app.on_event("startup")
async def seed_data():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Tenant).where(Tenant.slug == "default"))
        if not result.scalar_one_or_none():
            tenant = Tenant(name="Сестричество", slug="default", timezone="Europe/Moscow", settings={"auto_approve_registration": True})
            db.add(tenant)
            await db.commit()
            await db.refresh(tenant)

            admin = User(
                tenant_id=tenant.id,
                email="admin@example.com",
                role="coordinator",
                full_name="Главный координатор",
                password_hash=hash_password("admin123"),
            )
            db.add(admin)

            dept = Department(tenant_id=tenant.id, name="Терапия")
            db.add(dept)
            dept2 = Department(tenant_id=tenant.id, name="Хирургия")
            db.add(dept2)

            await db.commit()


@app.get("/health")
async def health_check():
    return {"status": "ok"}
