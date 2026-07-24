import pytest
from httpx import AsyncClient
from tests.conftest import seed_tenant, login, auth_header


async def setup_shift(client, db):
    await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    headers = auth_header(token)
    create_resp = await client.post("/api/v1/shifts/", json={
        "department_id": 1,
        "start_time": "2026-08-01T09:00:00",
        "end_time": "2026-08-01T15:00:00",
        "total_slots": 3,
    }, headers=headers)
    shift_id = create_resp.json()["id"]
    await client.patch(f"/api/v1/shifts/{shift_id}/publish", headers=headers)
    return shift_id, token


async def test_register_for_shift(client: AsyncClient, db):
    shift_id, _ = await setup_shift(client, db)
    vol_token = await login(client, "vol@test.com", "vol123")
    resp = await client.post("/api/v1/registrations/", json={"shift_id": shift_id}, headers=auth_header(vol_token))
    assert resp.status_code == 201
    assert resp.json()["status"] == "approved"


async def test_register_duplicate(client: AsyncClient, db):
    shift_id, _ = await setup_shift(client, db)
    vol_token = await login(client, "vol@test.com", "vol123")
    headers = auth_header(vol_token)
    await client.post("/api/v1/registrations/", json={"shift_id": shift_id}, headers=headers)
    resp = await client.post("/api/v1/registrations/", json={"shift_id": shift_id}, headers=headers)
    assert resp.status_code == 400


async def test_register_no_slots(client: AsyncClient, db):
    shift_id, _ = await setup_shift(client, db)
    for i in range(3):
        email = f"vol{i}@test.com"
        await client.post("/api/v1/auth/register", json={
            "email": email, "password": "pass123", "full_name": f"Vol {i}", "role": "volunteer",
        })
        vol_token = await login(client, email, "pass123")
        await client.post("/api/v1/registrations/", json={"shift_id": shift_id}, headers=auth_header(vol_token))
    await client.post("/api/v1/auth/register", json={
        "email": "vol4@test.com", "password": "pass123", "full_name": "Vol 4", "role": "volunteer",
    })
    vol_token = await login(client, "vol4@test.com", "pass123")
    resp = await client.post("/api/v1/registrations/", json={"shift_id": shift_id}, headers=auth_header(vol_token))
    assert resp.status_code == 400


async def test_cancel_registration(client: AsyncClient, db):
    shift_id, _ = await setup_shift(client, db)
    vol_token = await login(client, "vol@test.com", "vol123")
    vol_headers = auth_header(vol_token)
    reg_resp = await client.post("/api/v1/registrations/", json={"shift_id": shift_id}, headers=vol_headers)
    reg_id = reg_resp.json()["id"]
    resp = await client.patch(f"/api/v1/registrations/{reg_id}/cancel", headers=vol_headers)
    assert resp.status_code == 200


async def test_confirm_attendance(client: AsyncClient, db):
    shift_id, _ = await setup_shift(client, db)
    vol_token = await login(client, "vol@test.com", "vol123")
    vol_headers = auth_header(vol_token)
    reg_resp = await client.post("/api/v1/registrations/", json={"shift_id": shift_id}, headers=vol_headers)
    reg_id = reg_resp.json()["id"]
    resp = await client.patch(f"/api/v1/registrations/{reg_id}/confirm-attendance", headers=vol_headers)
    assert resp.status_code == 200


async def test_moderate_approve(client: AsyncClient, db):
    shift_id, coord_token = await setup_shift(client, db)
    vol_token = await login(client, "vol@test.com", "vol123")
    reg_resp = await client.post("/api/v1/registrations/", json={"shift_id": shift_id}, headers=auth_header(vol_token))
    reg_id = reg_resp.json()["id"]
    resp = await client.patch(f"/api/v1/registrations/{reg_id}/moderate", json={"status": "approved"}, headers=auth_header(coord_token))
    assert resp.status_code == 200


async def test_moderate_reject_with_comment(client: AsyncClient, db):
    shift_id, coord_token = await setup_shift(client, db)
    vol_token = await login(client, "vol@test.com", "vol123")
    reg_resp = await client.post("/api/v1/registrations/", json={"shift_id": shift_id}, headers=auth_header(vol_token))
    reg_id = reg_resp.json()["id"]
    resp = await client.patch(f"/api/v1/registrations/{reg_id}/moderate", json={
        "status": "rejected",
        "moderator_comment": "Не подходит по расписанию",
    }, headers=auth_header(coord_token))
    assert resp.status_code == 200


async def test_moderate_reject_without_comment(client: AsyncClient, db):
    shift_id, coord_token = await setup_shift(client, db)
    vol_token = await login(client, "vol@test.com", "vol123")
    reg_resp = await client.post("/api/v1/registrations/", json={"shift_id": shift_id}, headers=auth_header(vol_token))
    reg_id = reg_resp.json()["id"]
    resp = await client.patch(f"/api/v1/registrations/{reg_id}/moderate", json={"status": "rejected"}, headers=auth_header(coord_token))
    assert resp.status_code == 400


async def test_bulk_moderate(client: AsyncClient, db):
    shift_id, coord_token = await setup_shift(client, db)
    reg_ids = []
    for i in range(3):
        email = f"bulk{i}@test.com"
        await client.post("/api/v1/auth/register", json={
            "email": email, "password": "pass123", "full_name": f"Bulk {i}", "role": "volunteer",
        })
        vol_token = await login(client, email, "pass123")
        reg_resp = await client.post("/api/v1/registrations/", json={"shift_id": shift_id}, headers=auth_header(vol_token))
        reg_ids.append(reg_resp.json()["id"])
    resp = await client.post("/api/v1/registrations/bulk-moderate", json={
        "registration_ids": reg_ids,
        "approve": True,
    }, headers=auth_header(coord_token))
    assert resp.status_code == 200


async def test_my_registrations(client: AsyncClient, db):
    shift_id, _ = await setup_shift(client, db)
    vol_token = await login(client, "vol@test.com", "vol123")
    await client.post("/api/v1/registrations/", json={"shift_id": shift_id}, headers=auth_header(vol_token))
    resp = await client.get("/api/v1/registrations/my", headers=auth_header(vol_token))
    assert resp.status_code == 200
    assert len(resp.json()) >= 1
