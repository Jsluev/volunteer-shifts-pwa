from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog


async def log_action(
    db: AsyncSession,
    tenant_id: int,
    user_id: int,
    action_type: str,
    meta: dict | None = None,
):
    log = AuditLog(
        tenant_id=tenant_id,
        user_id=user_id,
        action_type=action_type,
        meta=meta or {},
    )
    db.add(log)
    await db.flush()
    return log
