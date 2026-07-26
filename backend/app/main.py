import asyncio
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from app.api.v1 import auth, shifts, registrations, departments, notifications, chat, analytics
from app.api.v1 import notification_settings
from app.models import Tenant, User, Department, Shift, ShiftRegistration, Dialog, ChatMessage, Notification, AuditLog
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.core.redis import rate_limit
from app.services.notifications import send_shift_reminders

reminder_task: asyncio.Task | None = None


async def _reminder_loop():
    while True:
        try:
            async with AsyncSessionLocal() as db:
                await send_shift_reminders(db)
        except Exception:
            pass
        await asyncio.sleep(300)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global reminder_task
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

    reminder_task = asyncio.create_task(_reminder_loop())
    yield
    if reminder_task:
        reminder_task.cancel()


app = FastAPI(
    title="Volunteer Shifts API",
    description="System for managing volunteer shifts in hospitals",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path.startswith("/api/v1/auth/"):
        client_ip = request.client.host if request.client else "unknown"
        key = f"{request.url.path}:{client_ip}"
        if not await rate_limit(key, limit=120, window=60):
            return Response(content='{"detail":"Too many requests"}', status_code=429, media_type="application/json")
    return await call_next(request)


app.include_router(auth.router, prefix="/api/v1")
app.include_router(departments.router, prefix="/api/v1")
app.include_router(shifts.router, prefix="/api/v1")
app.include_router(registrations.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(notification_settings.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok"}
