import pytest
from httpx import AsyncClient
from tests.conftest import seed_tenant, login, auth_header


async def test_register_user(client: AsyncClient, db):
    await seed_tenant(db)
    resp = await client.post("/api/v1/auth/register", json={
        "email": "new@test.com",
        "password": "pass123",
        "full_name": "New User",
        "role": "volunteer",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "new@test.com"
    assert data["role"] == "volunteer"
    assert "id" in data


async def test_register_duplicate_email(client: AsyncClient, db):
    await seed_tenant(db)
    await client.post("/api/v1/auth/register", json={
        "email": "dup@test.com",
        "password": "pass123",
        "full_name": "Dup User",
        "role": "volunteer",
    })
    resp = await client.post("/api/v1/auth/register", json={
        "email": "dup@test.com",
        "password": "pass456",
        "full_name": "Dup User 2",
        "role": "volunteer",
    })
    assert resp.status_code == 400


async def test_login_success(client: AsyncClient, db):
    await seed_tenant(db)
    await client.post("/api/v1/auth/register", json={
        "email": "login@test.com",
        "password": "pass123",
        "full_name": "Login User",
        "role": "volunteer",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "login@test.com",
        "password": "pass123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient, db):
    await seed_tenant(db)
    await client.post("/api/v1/auth/register", json={
        "email": "wrong@test.com",
        "password": "pass123",
        "full_name": "Wrong User",
        "role": "volunteer",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "wrong@test.com",
        "password": "wrongpass",
    })
    assert resp.status_code == 401


async def test_login_nonexistent_user(client: AsyncClient, db):
    await seed_tenant(db)
    resp = await client.post("/api/v1/auth/login", json={
        "email": "nobody@test.com",
        "password": "pass123",
    })
    assert resp.status_code == 401


async def test_get_me(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    resp = await client.get("/api/v1/auth/me", headers=auth_header(token))
    assert resp.status_code == 200
    assert resp.json()["email"] == "coord@test.com"


async def test_refresh_token(client: AsyncClient, db):
    await seed_tenant(db)
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": "coord@test.com",
        "password": "coord123",
    })
    refresh_token = login_resp.json()["refresh_token"]
    resp = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token,
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_unauthorized_access(client: AsyncClient, db):
    await seed_tenant(db)
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code in (401, 403)
