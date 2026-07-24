import pytest
from httpx import AsyncClient
from tests.conftest import seed_tenant, login, auth_header


async def test_list_departments(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    resp = await client.get("/api/v1/departments/", headers=auth_header(token))
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


async def test_create_department(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    resp = await client.post("/api/v1/departments/", json={"name": "Кардиология"}, headers=auth_header(token))
    assert resp.status_code == 201
    assert resp.json()["name"] == "Кардиология"


async def test_create_department_duplicate(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    await client.post("/api/v1/departments/", json={"name": "Дубль"}, headers=auth_header(token))
    resp = await client.post("/api/v1/departments/", json={"name": "Дубль"}, headers=auth_header(token))
    assert resp.status_code == 400


async def test_delete_department(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    create_resp = await client.post("/api/v1/departments/", json={"name": "Удаляемое"}, headers=auth_header(token))
    dept_id = create_resp.json()["id"]
    resp = await client.delete(f"/api/v1/departments/{dept_id}", headers=auth_header(token))
    assert resp.status_code == 200


async def test_volunteer_cannot_create_department(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "vol@test.com", "vol123")
    resp = await client.post("/api/v1/departments/", json={"name": "Запрещ"}, headers=auth_header(token))
    assert resp.status_code == 403
