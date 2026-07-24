import pytest
from httpx import AsyncClient
from tests.conftest import seed_tenant, login, auth_header


async def test_create_shift(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    headers = auth_header(token)
    resp = await client.post("/api/v1/shifts/", json={
        "department_id": 1,
        "start_time": "2026-08-01T09:00:00",
        "end_time": "2026-08-01T15:00:00",
        "total_slots": 5,
    }, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["status"] == "draft"
    assert resp.json()["total_slots"] == 5


async def test_create_shift_invalid_department(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    resp = await client.post("/api/v1/shifts/", json={
        "department_id": 999,
        "start_time": "2026-08-01T09:00:00",
        "end_time": "2026-08-01T15:00:00",
        "total_slots": 5,
    }, headers=auth_header(token))
    assert resp.status_code == 404


async def test_create_shift_invalid_time(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    resp = await client.post("/api/v1/shifts/", json={
        "department_id": 1,
        "start_time": "2026-08-01T15:00:00",
        "end_time": "2026-08-01T09:00:00",
        "total_slots": 5,
    }, headers=auth_header(token))
    assert resp.status_code == 400


async def test_create_shift_volunteer_forbidden(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "vol@test.com", "vol123")
    resp = await client.post("/api/v1/shifts/", json={
        "department_id": 1,
        "start_time": "2026-08-01T09:00:00",
        "end_time": "2026-08-01T15:00:00",
        "total_slots": 5,
    }, headers=auth_header(token))
    assert resp.status_code == 403


async def test_publish_shift(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    headers = auth_header(token)
    create_resp = await client.post("/api/v1/shifts/", json={
        "department_id": 1,
        "start_time": "2026-08-01T09:00:00",
        "end_time": "2026-08-01T15:00:00",
        "total_slots": 5,
    }, headers=headers)
    shift_id = create_resp.json()["id"]
    resp = await client.patch(f"/api/v1/shifts/{shift_id}/publish", headers=headers)
    assert resp.status_code == 200


async def test_publish_already_published(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    headers = auth_header(token)
    create_resp = await client.post("/api/v1/shifts/", json={
        "department_id": 1,
        "start_time": "2026-08-01T09:00:00",
        "end_time": "2026-08-01T15:00:00",
        "total_slots": 5,
    }, headers=headers)
    shift_id = create_resp.json()["id"]
    await client.patch(f"/api/v1/shifts/{shift_id}/publish", headers=headers)
    resp = await client.patch(f"/api/v1/shifts/{shift_id}/publish", headers=headers)
    assert resp.status_code == 400


async def test_cancel_shift(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    headers = auth_header(token)
    create_resp = await client.post("/api/v1/shifts/", json={
        "department_id": 1,
        "start_time": "2026-08-01T09:00:00",
        "end_time": "2026-08-01T15:00:00",
        "total_slots": 5,
    }, headers=headers)
    shift_id = create_resp.json()["id"]
    resp = await client.patch(f"/api/v1/shifts/{shift_id}/cancel", headers=headers)
    assert resp.status_code == 200


async def test_delete_shift(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    headers = auth_header(token)
    create_resp = await client.post("/api/v1/shifts/", json={
        "department_id": 1,
        "start_time": "2026-08-01T09:00:00",
        "end_time": "2026-08-01T15:00:00",
        "total_slots": 5,
    }, headers=headers)
    shift_id = create_resp.json()["id"]
    resp = await client.delete(f"/api/v1/shifts/{shift_id}", headers=headers)
    assert resp.status_code == 200


async def test_update_shift_slots(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    headers = auth_header(token)
    create_resp = await client.post("/api/v1/shifts/", json={
        "department_id": 1,
        "start_time": "2026-08-01T09:00:00",
        "end_time": "2026-08-01T15:00:00",
        "total_slots": 5,
    }, headers=headers)
    shift_id = create_resp.json()["id"]
    resp = await client.put(f"/api/v1/shifts/{shift_id}", json={"total_slots": 10}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["total_slots"] == 10


async def test_list_shifts(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    headers = auth_header(token)
    create_resp = await client.post("/api/v1/shifts/", json={
        "department_id": 1,
        "start_time": "2026-08-01T09:00:00",
        "end_time": "2026-08-01T15:00:00",
        "total_slots": 5,
    }, headers=headers)
    shift_id = create_resp.json()["id"]
    await client.patch(f"/api/v1/shifts/{shift_id}/publish", headers=headers)
    resp = await client.get("/api/v1/shifts/", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


async def test_shift_registrations_list(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    headers = auth_header(token)
    create_resp = await client.post("/api/v1/shifts/", json={
        "department_id": 1,
        "start_time": "2026-08-01T09:00:00",
        "end_time": "2026-08-01T15:00:00",
        "total_slots": 5,
    }, headers=headers)
    shift_id = create_resp.json()["id"]
    await client.patch(f"/api/v1/shifts/{shift_id}/publish", headers=headers)
    vol_token = await login(client, "vol@test.com", "vol123")
    await client.post("/api/v1/registrations/", json={"shift_id": shift_id}, headers=auth_header(vol_token))
    resp = await client.get(f"/api/v1/shifts/{shift_id}/registrations", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1
