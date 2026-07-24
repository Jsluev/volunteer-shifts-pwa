import pytest
from httpx import AsyncClient
from tests.conftest import seed_tenant, login, auth_header


async def test_list_notifications(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "vol@test.com", "vol123")
    resp = await client.get("/api/v1/notifications/", headers=auth_header(token))
    assert resp.status_code == 200


async def test_unread_count(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "vol@test.com", "vol123")
    resp = await client.get("/api/v1/notifications/unread-count", headers=auth_header(token))
    assert resp.status_code == 200
    assert "count" in resp.json()


async def test_broadcast(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    resp = await client.post("/api/v1/notifications/broadcast", json={
        "message": "Важное сообщение",
        "target": "all",
        "priority": "high",
    }, headers=auth_header(token))
    assert resp.status_code == 200
    assert "users" in resp.json()["message"]


async def test_volunteer_cannot_broadcast(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "vol@test.com", "vol123")
    resp = await client.post("/api/v1/notifications/broadcast", json={
        "message": "Спам",
        "target": "all",
    }, headers=auth_header(token))
    assert resp.status_code == 403


async def test_notification_settings_get(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "vol@test.com", "vol123")
    resp = await client.get("/api/v1/notification-settings/", headers=auth_header(token))
    assert resp.status_code == 200
    assert "email_enabled" in resp.json()


async def test_notification_settings_update(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "vol@test.com", "vol123")
    resp = await client.put("/api/v1/notification-settings/", json={
        "email_enabled": False,
        "push_enabled": True,
        "inapp_enabled": True,
        "sms_enabled": False,
        "reminder_2days": True,
        "reminder_15hours": False,
        "reminder_1hour": True,
        "quiet_hours_start": 2,
        "quiet_hours_end": 8,
    }, headers=auth_header(token))
    assert resp.status_code == 200
    assert resp.json()["email_enabled"] is False


async def test_trigger_reminders(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    resp = await client.post("/api/v1/notifications/trigger-reminders", headers=auth_header(token))
    assert resp.status_code == 200
