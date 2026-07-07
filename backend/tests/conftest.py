import os

# Must be set before importing app modules (settings fail fast on missing config)
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite://")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("CORS_ORIGINS", "http://testserver")

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from core import template_store
from database import Base, get_db
from models.compendium import Compendium, CompendiumEntry, GuidRedirect
from models.system import System
from models.template import EntryTemplate
from schemas.systems import dnd50
from main import app

# Only the tables under test — actor/campaign/user models use PG-only column
# types and aren't covered by the Phase 0/1 suites.
TEST_TABLES = [System.__table__, Compendium.__table__, CompendiumEntry.__table__,
               GuidRedirect.__table__, EntryTemplate.__table__]


@pytest.fixture
async def db_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: Base.metadata.create_all(c, tables=TEST_TABLES))
    # Seed the d&d5.0 system + its entry-type templates, mirroring what
    # seed_data.py does on startup (entry_templates is the runtime source
    # of truth for schemas — see core/template_store.py).
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as session:
        session.add(System(
            guid=dnd50.SYSTEM_INFO["guid"],
            name=dnd50.SYSTEM_INFO["name"],
            description=dnd50.SYSTEM_INFO.get("description"),
            link=dnd50.SYSTEM_INFO.get("link"),
        ))
        for entry_type, registration in dnd50.SCHEMAS.items():
            session.add(EntryTemplate(
                system=registration.system,
                entry_type=entry_type,
                fields=template_store.fields_from_registration(registration),
            ))
        await session.commit()
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine):
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as session:
        yield session


@pytest.fixture
async def client(db_engine):
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.clear()
