from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from app.models.shift import Shift
from app.models.registration import ShiftRegistration
from app.models.user import User
from app.models.notification import Notification
from app.services.email import send_email


async def create_notification(
    db: AsyncSession,
    user_id: int,
    notif_type: str,
    channel: str,
    subject: str | None,
    body: str,
    scheduled_at: datetime | None = None,
):
    notif = Notification(
        user_id=user_id,
        type=notif_type,
        channel=channel,
        subject=subject,
        body=body,
        scheduled_at=scheduled_at or func.now(),
        status="pending",
    )
    db.add(notif)
    await db.flush()

    if channel == "email":
        user = await db.execute(select(User).where(User.id == user_id))
        user_obj = user.scalar_one_or_none()
        if user_obj and user_obj.email:
            sent = send_email(user_obj.email, subject or "Уведомление", body)
            if sent:
                notif.status = "sent"
                notif.sent_at = datetime.utcnow()

    return notif


async def send_shift_reminders(db: AsyncSession):
    now = datetime.utcnow()
    reminders = [
        (timedelta(days=2), "За 2 дня до смены"),
        (timedelta(hours=15), "Через 15 часов"),
        (timedelta(hours=1, minutes=30), "Скоро начинается смена"),
    ]

    for delta, label in reminders:
        target = now + delta
        window_start = target - timedelta(minutes=30)
        window_end = target + timedelta(minutes=30)

        shifts = await db.execute(
            select(Shift).where(
                Shift.status == "published",
                Shift.start_time >= window_start,
                Shift.start_time <= window_end,
            )
        )

        for shift in shifts.scalars().all():
            registrations = await db.execute(
                select(ShiftRegistration).where(
                    ShiftRegistration.shift_id == shift.id,
                    ShiftRegistration.status.in_(["approved", "attendance_confirmed"]),
                )
            )

            for reg in registrations.scalars().all():
                existing = await db.execute(
                    select(Notification).where(
                        Notification.user_id == reg.user_id,
                        Notification.type == "reminder",
                        Notification.body.contains(f"смена #{shift.id}"),
                    )
                )
                if existing.scalar_one_or_none():
                    continue

                await create_notification(
                    db,
                    user_id=reg.user_id,
                    notif_type="reminder",
                    channel="inapp",
                    subject=label,
                    body=f"Напоминание: ваша смена #{shift.id} начинается {shift.start_time.strftime('%d.%m.%Y в %H:%M')}",
                    scheduled_at=now,
                )

    await db.commit()


async def create_broadcast(
    db: AsyncSession,
    tenant_id: int,
    sender_id: int,
    message: str,
    target: str,
    department_id: int | None = None,
    priority: str = "normal",
):
    query = select(User).where(User.tenant_id == tenant_id, User.is_active == True)

    if target == "department" and department_id:
        query = query.where(User.role == "volunteer")

    users = await db.execute(query)
    count = 0
    for user in users.scalars().all():
        await create_notification(
            db,
            user_id=user.id,
            notif_type="broadcast",
            channel="inapp",
            subject=f"Сообщение от координатора [{priority.upper()}]" if priority == "high" else "Сообщение от координатора",
            body=message,
        )
        count += 1

    await db.commit()
    return count
