import pytest
from httpx import AsyncClient
from tests.conftest import seed_tenant, login, auth_header


async def test_fill_rate(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    resp = await client.get("/api/v1/analytics/fill-rate", headers=auth_header(token))
    assert resp.status_code == 200
    assert "total_shifts" in resp.json()
    assert "fill_rate_percent" in resp.json()


async def test_volunteer_stats(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    resp = await client.get("/api/v1/analytics/volunteer-stats/3", headers=auth_header(token))
    assert resp.status_code == 200
    assert "total_registrations" in resp.json()
    assert "attendance_rate" in resp.json()


async def test_volunteer_classification(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    resp = await client.get("/api/v1/analytics/volunteer-classification", headers=auth_header(token))
    assert resp.status_code == 200
    assert "total_volunteers" in resp.json()
    assert "classifications" in resp.json()


async def test_unfilled_slots(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    resp = await client.get("/api/v1/analytics/unfilled-slots", headers=auth_header(token))
    assert resp.status_code == 200
    assert "shifts" in resp.json()


async def test_audit_log(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    headers = auth_header(token)
    await client.post("/api/v1/shifts/", json={
        "department_id": 1,
        "start_time": "2026-08-01T09:00:00",
        "end_time": "2026-08-01T15:00:00",
        "total_slots": 5,
    }, headers=headers)
    resp = await client.get("/api/v1/analytics/audit", headers=headers)
    assert resp.status_code == 200
    assert "logs" in resp.json()
    assert resp.json()["total"] >= 1


async def test_audit_filter_by_action(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    headers = auth_header(token)
    await client.post("/api/v1/shifts/", json={
        "department_id": 1,
        "start_time": "2026-08-01T09:00:00",
        "end_time": "2026-08-01T15:00:00",
        "total_slots": 5,
    }, headers=headers)
    resp = await client.get("/api/v1/analytics/audit?action_type=create_shift", headers=headers)
    assert resp.status_code == 200
    for log in resp.json()["logs"]:
        assert log["action_type"] == "create_shift"


async def test_volunteer_cannot_access_analytics(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "vol@test.com", "vol123")
    resp = await client.get("/api/v1/analytics/fill-rate", headers=auth_header(token))
    assert resp.status_code == 403
