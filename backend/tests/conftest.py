import asyncio
import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.database import Base, get_db
from app.main import app
from app.core.security import hash_password

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@db:5432/volunteer_shifts_test"
)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def test_session_factory(test_engine):
    return async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_database(test_engine):
    async with test_engine.connect() as conn:
        await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.commit()
    async with test_engine.connect() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.commit()
    yield
    async with test_engine.connect() as conn:
        await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.commit()


@pytest_asyncio.fixture
async def db(test_session_factory):
    async with test_session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(test_session_factory):
    async def override_get_db():
        async with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


async def seed_tenant(db: AsyncSession):
    from app.models.tenant import Tenant
    from app.models.user import User
    from app.models.department import Department

    tenant = Tenant(name="Тест", slug="test", timezone="Europe/Moscow", settings={"auto_approve_registration": True})
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)

    coordinator = User(
        tenant_id=tenant.id,
        email="coord@test.com",
        role="coordinator",
        full_name="Тест Координатор",
        password_hash=hash_password("coord123"),
        settings={},
    )
    db.add(coordinator)

    volunteer = User(
        tenant_id=tenant.id,
        email="vol@test.com",
        role="volunteer",
        full_name="Тест Волонтёр",
        password_hash=hash_password("vol123"),
        settings={},
    )
    db.add(volunteer)

    controller = User(
        tenant_id=tenant.id,
        email="ctrl@test.com",
        role="controller",
        full_name="Тест Контролёр",
        password_hash=hash_password("ctrl123"),
        settings={},
    )
    db.add(controller)

    dept = Department(tenant_id=tenant.id, name="Терапия")
    db.add(dept)
    dept2 = Department(tenant_id=tenant.id, name="Хирургия")
    db.add(dept2)

    await db.commit()
    await db.refresh(tenant)
    await db.refresh(coordinator)
    await db.refresh(volunteer)
    await db.refresh(controller)

    return {
        "tenant": tenant,
        "coordinator": coordinator,
        "volunteer": volunteer,
        "controller": controller,
        "departments": [dept, dept2],
    }


async def register_user(client: AsyncClient, email: str, password: str, role: str = "volunteer"):
    resp = await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "full_name": f"User {email}",
        "role": role,
    })
    return resp


async def login(client: AsyncClient, email: str, password: str):
    resp = await client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password,
    })
    data = resp.json()
    return data.get("access_token")


def auth_header(token: str):
    return {"Authorization": f"Bearer {token}"}
