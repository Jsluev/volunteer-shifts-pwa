import pytest
from httpx import AsyncClient
from tests.conftest import seed_tenant, login, auth_header


async def test_empty_shifts_list(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    resp = await client.get("/api/v1/shifts/?status=published", headers=auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


async def test_empty_notifications_list(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "vol@test.com", "vol123")
    resp = await client.get("/api/v1/notifications/", headers=auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


async def test_empty_dialogs_list(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "vol@test.com", "vol123")
    resp = await client.get("/api/v1/chat/dialogs", headers=auth_header(token))
    assert resp.status_code == 200
    assert resp.json() == []


async def test_invalid_jwt_token(client: AsyncClient, db):
    await seed_tenant(db)
    resp = await client.get(
        "/api/v1/shifts/",
        headers={"Authorization": "Bearer invalid.jwt.token"},
    )
    assert resp.status_code in (401, 403)


async def test_expired_jwt_token(client: AsyncClient, db):
    await seed_tenant(db)
    from app.core.security import create_access_token
    from datetime import timedelta
    token = create_access_token({"sub": "9999", "tenant_id": 1, "role": "volunteer"}, expires_delta=timedelta(seconds=-10))
    resp = await client.get(
        "/api/v1/shifts/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code in (401, 403)


async def test_refresh_with_access_token(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "vol@test.com", "vol123")
    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": token},
    )
    assert resp.status_code == 401


async def test_create_shift_invalid_slots(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    resp = await client.post(
        "/api/v1/shifts/",
        json={
            "department_id": 1,
            "start_time": "2026-01-01T10:00:00",
            "end_time": "2026-01-01T08:00:00",
            "total_slots": 0,
        },
        headers=auth_header(token),
    )
    assert resp.status_code in (400, 422)


async def test_get_nonexistent_shift_registrations(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    resp = await client.get(
        "/api/v1/shifts/9999/registrations",
        headers=auth_header(token),
    )
    assert resp.status_code == 200
    assert resp.json() == []


async def test_moderate_nonexistent_registration(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    resp = await client.patch(
        "/api/v1/registrations/9999/moderate",
        json={"status": "approved"},
        headers=auth_header(token),
    )
    assert resp.status_code == 404


async def test_send_empty_message(client: AsyncClient, db):
    data = await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    coord_id = data["coordinator"].id
    vol_id = data["volunteer"].id
    dialog_resp = await client.post("/api/v1/chat/dialogs", json={
        "type": "personal",
        "participant_ids": [coord_id, vol_id],
    }, headers=auth_header(token))
    dialog_id = dialog_resp.json()["id"]
    resp = await client.post("/api/v1/chat/messages", json={
        "dialog_id": dialog_id,
        "text": "",
    }, headers=auth_header(token))
    assert resp.status_code == 400


async def test_create_dialog_with_nonexistent_user(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    resp = await client.post("/api/v1/chat/dialogs", json={
        "type": "personal",
        "participant_ids": [9999],
    }, headers=auth_header(token))
    assert resp.status_code == 404


async def test_shifts_pagination(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    for i in range(3):
        resp = await client.post("/api/v1/shifts/", json={
            "department_id": 1,
            "start_time": f"2026-08-{10+i}T10:00:00",
            "end_time": f"2026-08-{10+i}T18:00:00",
            "total_slots": 5,
        }, headers=auth_header(token))
        shift_id = resp.json()["id"]
        await client.patch(f"/api/v1/shifts/{shift_id}/publish", headers=auth_header(token))
    resp = await client.get("/api/v1/shifts/?limit=2&offset=0", headers=auth_header(token))
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["total"] == 3
    assert data["offset"] == 0
    assert data["limit"] == 2
