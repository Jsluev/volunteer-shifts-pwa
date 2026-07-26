import pytest
from httpx import AsyncClient
from tests.conftest import seed_tenant, login, auth_header


async def test_export_fill_rate(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    resp = await client.get("/api/v1/analytics/export/fill-rate", headers=auth_header(token))
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    content = resp.text
    assert "Shift ID" in content


async def test_export_unfilled(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    resp = await client.get("/api/v1/analytics/export/unfilled-slots", headers=auth_header(token))
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]


async def test_export_classification(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    resp = await client.get("/api/v1/analytics/export/volunteer-classification", headers=auth_header(token))
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    content = resp.text
    assert "User ID" in content


async def test_export_volunteer_forbidden(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "vol@test.com", "vol123")
    resp = await client.get("/api/v1/analytics/export/fill-rate", headers=auth_header(token))
    assert resp.status_code == 403
