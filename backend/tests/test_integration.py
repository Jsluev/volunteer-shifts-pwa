import pytest
from httpx import AsyncClient
from tests.conftest import seed_tenant, login, auth_header


async def test_full_coordinator_workflow(client: AsyncClient, db):
    data = await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    headers = auth_header(token)
    coord_id = data["coordinator"].id
    vol_id = data["volunteer"].id

    dept_resp = await client.get("/api/v1/departments/", headers=headers)
    dept_id = dept_resp.json()[0]["id"]

    shift_resp = await client.post("/api/v1/shifts/", json={
        "department_id": dept_id,
        "start_time": "2026-09-01T09:00:00",
        "end_time": "2026-09-01T17:00:00",
        "total_slots": 3,
    }, headers=headers)
    assert shift_resp.status_code == 201
    shift_id = shift_resp.json()["id"]

    publish_resp = await client.patch(f"/api/v1/shifts/{shift_id}/publish", headers=headers)
    assert publish_resp.status_code == 200

    list_resp = await client.get("/api/v1/shifts/?status=published", headers=headers)
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] >= 1

    vol_token = await login(client, "vol@test.com", "vol123")
    vol_headers = auth_header(vol_token)
    reg_resp = await client.post("/api/v1/registrations/", json={
        "shift_id": shift_id,
    }, headers=vol_headers)
    assert reg_resp.status_code == 201
    reg_id = reg_resp.json()["id"]

    my_regs = await client.get("/api/v1/registrations/my", headers=vol_headers)
    assert my_regs.status_code == 200

    mod_resp = await client.patch(f"/api/v1/registrations/{reg_id}/moderate", json={
        "status": "approved",
        "moderator_comment": "Одобрено",
    }, headers=headers)
    assert mod_resp.status_code == 200

    fill_rate = await client.get("/api/v1/analytics/fill-rate", headers=headers)
    assert fill_rate.status_code == 200
    assert fill_rate.json()["filled_slots"] >= 1

    unfilled = await client.get("/api/v1/analytics/unfilled-slots", headers=headers)
    assert unfilled.status_code == 200

    audit = await client.get("/api/v1/analytics/audit", headers=headers)
    assert audit.status_code == 200
    assert audit.json()["total"] >= 1

    export_resp = await client.get("/api/v1/analytics/export/fill-rate", headers=headers)
    assert export_resp.status_code == 200
    assert "text/csv" in export_resp.headers["content-type"]


async def test_full_chat_workflow(client: AsyncClient, db):
    data = await seed_tenant(db)
    coord_token = await login(client, "coord@test.com", "coord123")
    vol_token = await login(client, "vol@test.com", "vol123")
    coord_id = data["coordinator"].id
    vol_id = data["volunteer"].id

    dialog_resp = await client.post("/api/v1/chat/dialogs", json={
        "type": "personal",
        "participant_ids": [coord_id, vol_id],
    }, headers=auth_header(coord_token))
    assert dialog_resp.status_code == 201
    dialog_id = dialog_resp.json()["id"]

    msg1 = await client.post("/api/v1/chat/messages", json={
        "dialog_id": dialog_id,
        "text": "Привет от координатора!",
    }, headers=auth_header(coord_token))
    assert msg1.status_code == 201

    msg2 = await client.post("/api/v1/chat/messages", json={
        "dialog_id": dialog_id,
        "text": "Привет от волонтёра!",
    }, headers=auth_header(vol_token))
    assert msg2.status_code == 201

    msgs = await client.get(f"/api/v1/chat/dialogs/{dialog_id}/messages", headers=auth_header(vol_token))
    assert msgs.status_code == 200
    assert len(msgs.json()) == 2

    vol_dialogs = await client.get("/api/v1/chat/dialogs", headers=auth_header(vol_token))
    assert vol_dialogs.status_code == 200
    assert len(vol_dialogs.json()) >= 1

    access_resp = await client.get(f"/api/v1/chat/dialogs/{dialog_id}/messages", headers=auth_header(coord_token))
    assert access_resp.status_code == 200

    ctrl_token = await login(client, "ctrl@test.com", "ctrl123")
    denied_resp = await client.get(f"/api/v1/chat/dialogs/{dialog_id}/messages", headers=auth_header(ctrl_token))
    assert denied_resp.status_code == 403


async def test_notification_flow(client: AsyncClient, db):
    data = await seed_tenant(db)
    vol_token = await login(client, "vol@test.com", "vol123")
    coord_token = await login(client, "coord@test.com", "coord123")

    notifs = await client.get("/api/v1/notifications/", headers=auth_header(vol_token))
    assert notifs.status_code == 200
    assert notifs.json()["total"] == 0

    broadcast = await client.post("/api/v1/notifications/broadcast", json={
        "message": "Важное объявление!",
        "target": "all",
        "priority": "high",
    }, headers=auth_header(coord_token))
    assert broadcast.status_code == 200

    notifs_after = await client.get("/api/v1/notifications/", headers=auth_header(vol_token))
    assert notifs_after.json()["total"] >= 1

    unread = await client.get("/api/v1/notifications/unread-count", headers=auth_header(vol_token))
    assert unread.json()["count"] >= 1


async def test_registration_lifecycle(client: AsyncClient, db):
    data = await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")
    vol_token = await login(client, "vol@test.com", "vol123")

    dept_resp = await client.get("/api/v1/departments/", headers=auth_header(token))
    dept_id = dept_resp.json()[0]["id"]

    shift_resp = await client.post("/api/v1/shifts/", json={
        "department_id": dept_id,
        "start_time": "2026-10-01T09:00:00",
        "end_time": "2026-10-01T17:00:00",
        "total_slots": 2,
    }, headers=auth_header(token))
    shift_id = shift_resp.json()["id"]
    await client.patch(f"/api/v1/shifts/{shift_id}/publish", headers=auth_header(token))

    reg = await client.post("/api/v1/registrations/", json={"shift_id": shift_id}, headers=auth_header(vol_token))
    reg_id = reg.json()["id"]

    cancel = await client.patch(f"/api/v1/registrations/{reg_id}/cancel", headers=auth_header(vol_token))
    assert cancel.status_code == 200

    shift2_resp = await client.post("/api/v1/shifts/", json={
        "department_id": dept_id,
        "start_time": "2026-10-02T09:00:00",
        "end_time": "2026-10-02T17:00:00",
        "total_slots": 2,
    }, headers=auth_header(token))
    shift2_id = shift2_resp.json()["id"]
    await client.patch(f"/api/v1/shifts/{shift2_id}/publish", headers=auth_header(token))

    reg2 = await client.post("/api/v1/registrations/", json={"shift_id": shift2_id}, headers=auth_header(vol_token))
    reg2_id = reg2.json()["id"]

    approve = await client.patch(f"/api/v1/registrations/{reg2_id}/moderate", json={
        "status": "approved",
    }, headers=auth_header(token))
    assert approve.status_code == 200

    confirm = await client.patch(f"/api/v1/registrations/{reg2_id}/confirm-attendance", headers=auth_header(vol_token))
    assert confirm.status_code == 200

    shift_regs = await client.get(f"/api/v1/shifts/{shift2_id}/registrations", headers=auth_header(token))
    assert shift_regs.status_code == 200


async def test_department_crud(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")

    create = await client.post("/api/v1/departments/", json={"name": "Неврология"}, headers=auth_header(token))
    assert create.status_code == 201

    dup = await client.post("/api/v1/departments/", json={"name": "Неврология"}, headers=auth_header(token))
    assert dup.status_code == 400

    depts = await client.get("/api/v1/departments/", headers=auth_header(token))
    assert depts.status_code == 200
    assert len(depts.json()) >= 3

    vol_token = await login(client, "vol@test.com", "vol123")
    vol_create = await client.post("/api/v1/departments/", json={"name": "Test"}, headers=auth_header(vol_token))
    assert vol_create.status_code == 403


async def test_shift_lifecycle(client: AsyncClient, db):
    await seed_tenant(db)
    token = await login(client, "coord@test.com", "coord123")

    dept_resp = await client.get("/api/v1/departments/", headers=auth_header(token))
    dept_id = dept_resp.json()[0]["id"]

    shift = await client.post("/api/v1/shifts/", json={
        "department_id": dept_id,
        "start_time": "2026-11-01T09:00:00",
        "end_time": "2026-11-01T17:00:00",
        "total_slots": 5,
    }, headers=auth_header(token))
    shift_id = shift.json()["id"]
    assert shift.json()["status"] == "draft"

    publish = await client.patch(f"/api/v1/shifts/{shift_id}/publish", headers=auth_header(token))
    assert publish.status_code == 200

    cancel = await client.patch(f"/api/v1/shifts/{shift_id}/cancel", headers=auth_header(token))
    assert cancel.status_code == 200

    shift2 = await client.post("/api/v1/shifts/", json={
        "department_id": dept_id,
        "start_time": "2026-12-01T09:00:00",
        "end_time": "2026-12-01T17:00:00",
        "total_slots": 5,
    }, headers=auth_header(token))
    shift2_id = shift2.json()["id"]
    await client.patch(f"/api/v1/shifts/{shift2_id}/publish", headers=auth_header(token))

    delete = await client.delete(f"/api/v1/shifts/{shift2_id}", headers=auth_header(token))
    assert delete.status_code == 200


async def test_auth_edge_cases(client: AsyncClient, db):
    await seed_tenant(db)

    reg = await client.post("/api/v1/auth/register", json={
        "email": "new@test.com",
        "password": "pass123",
        "full_name": "New User",
        "role": "volunteer",
    })
    assert reg.status_code == 201

    dup = await client.post("/api/v1/auth/register", json={
        "email": "new@test.com",
        "password": "pass123",
        "full_name": "New User",
        "role": "volunteer",
    })
    assert dup.status_code == 400

    login_resp = await client.post("/api/v1/auth/login", json={
        "email": "new@test.com",
        "password": "pass123",
    })
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    refresh = login_resp.json()["refresh_token"]

    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "new@test.com"

    refresh_resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert refresh_resp.status_code == 200

    wrong_pass = await client.post("/api/v1/auth/login", json={
        "email": "new@test.com",
        "password": "wrong",
    })
    assert wrong_pass.status_code == 401

    no_token = await client.get("/api/v1/shifts/")
    assert no_token.status_code in (401, 403)
