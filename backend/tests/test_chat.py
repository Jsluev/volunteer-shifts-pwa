import pytest
from httpx import AsyncClient
from tests.conftest import seed_tenant, login, auth_header


async def test_create_dialog(client: AsyncClient, db):
    data = await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    coord_id = data["coordinator"].id
    vol_id = data["volunteer"].id
    resp = await client.post("/api/v1/chat/dialogs", json={
        "type": "personal",
        "participant_ids": [coord_id, vol_id],
    }, headers=auth_header(token))
    assert resp.status_code == 201
    assert resp.json()["type"] == "personal"


async def test_list_dialogs(client: AsyncClient, db):
    data = await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    coord_id = data["coordinator"].id
    vol_id = data["volunteer"].id
    await client.post("/api/v1/chat/dialogs", json={
        "type": "personal",
        "participant_ids": [coord_id, vol_id],
    }, headers=auth_header(token))
    resp = await client.get("/api/v1/chat/dialogs", headers=auth_header(token))
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


async def test_send_message(client: AsyncClient, db):
    data = await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    headers = auth_header(token)
    coord_id = data["coordinator"].id
    vol_id = data["volunteer"].id
    dialog_resp = await client.post("/api/v1/chat/dialogs", json={
        "type": "personal",
        "participant_ids": [coord_id, vol_id],
    }, headers=headers)
    dialog_id = dialog_resp.json()["id"]
    resp = await client.post("/api/v1/chat/messages", json={
        "dialog_id": dialog_id,
        "text": "Привет!",
    }, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["text"] == "Привет!"


async def test_list_messages(client: AsyncClient, db):
    data = await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    headers = auth_header(token)
    coord_id = data["coordinator"].id
    vol_id = data["volunteer"].id
    dialog_resp = await client.post("/api/v1/chat/dialogs", json={
        "type": "personal",
        "participant_ids": [coord_id, vol_id],
    }, headers=headers)
    dialog_id = dialog_resp.json()["id"]
    await client.post("/api/v1/chat/messages", json={"dialog_id": dialog_id, "text": "Сообщение 1"}, headers=headers)
    await client.post("/api/v1/chat/messages", json={"dialog_id": dialog_id, "text": "Сообщение 2"}, headers=headers)
    resp = await client.get(f"/api/v1/chat/dialogs/{dialog_id}/messages", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


async def test_empty_message_rejected(client: AsyncClient, db):
    data = await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    headers = auth_header(token)
    coord_id = data["coordinator"].id
    vol_id = data["volunteer"].id
    dialog_resp = await client.post("/api/v1/chat/dialogs", json={
        "type": "personal",
        "participant_ids": [coord_id, vol_id],
    }, headers=headers)
    dialog_id = dialog_resp.json()["id"]
    resp = await client.post("/api/v1/chat/messages", json={
        "dialog_id": dialog_id,
        "text": "   ",
    }, headers=headers)
    assert resp.status_code == 400


async def test_access_denied_other_dialog(client: AsyncClient, db):
    data = await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    coord_id = data["coordinator"].id
    dialog_resp = await client.post("/api/v1/chat/dialogs", json={
        "type": "personal",
        "participant_ids": [coord_id],
    }, headers=auth_header(token))
    dialog_id = dialog_resp.json()["id"]
    vol_token = await login(client, "vol@test.com", "vol123")
    resp = await client.get(f"/api/v1/chat/dialogs/{dialog_id}/messages", headers=auth_header(vol_token))
    assert resp.status_code == 403
