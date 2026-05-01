import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_db, verify_api_key
from app.database import Base
from app.main import app

# ── In-memory SQLite for tests ────────────────────────────────────────────────
# StaticPool ensures all connections share the SAME in-memory database so that
# tables created by create_all() are visible to every subsequent query.

TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=test_engine
)

TEST_API_KEY = "nequi-secret-key-change-in-production"


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="function")
def db_session():
    """Fresh in-memory database per test function."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """TestClient with overridden DB and auth dependencies."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_verify_api_key():
        return None

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[verify_api_key] = override_verify_api_key

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def authed_client(db_session):
    """TestClient that uses the real API key verification (for auth tests)."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


# ── Shared helpers ────────────────────────────────────────────────────────────

VALID_PAYLOAD = {
    "message_id": "msg-test-001",
    "session_id": "session-abc",
    "content": "Hola, ¿cómo puedo ayudarte hoy?",
    "timestamp": "2024-01-15T14:30:00Z",
    "sender": "system",
}
