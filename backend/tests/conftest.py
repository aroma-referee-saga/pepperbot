import pytest
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from src.database import Base, get_db
from src.main import app
from src import models
from config.settings import settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_db():
    """Create a test database."""
    # Use in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_db):
    """Provide a database session for each test."""
    yield test_db


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with a mocked database session."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_scraper():
    """Mock scraper for testing."""
    mock = MagicMock()
    mock.scrape_and_store = MagicMock(return_value=None)
    return mock


@pytest.fixture
def mock_bot():
    """Mock bot for testing."""
    mock = MagicMock()
    mock.send_message = MagicMock(return_value=None)
    return mock


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing."""
    user = models.User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashedpassword123"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_discount(db_session):
    """Create a sample discount for testing."""
    discount = models.Discount(
        title="Test Discount",
        description="A test discount",
        store="Test Store",
        original_price=100.0,
        discount_price=80.0,
        discount_percentage=20.0
    )
    db_session.add(discount)
    db_session.commit()
    db_session.refresh(discount)
    return discount


@pytest.fixture
def auth_headers(sample_user):
    """Generate authentication headers for testing."""
    from src.auth import create_access_token
    access_token = create_access_token(data={"sub": sample_user.username})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def mock_httpx():
    """Mock httpx for external API calls."""
    with pytest.mock.patch('httpx.AsyncClient') as mock:
        yield mock


@pytest.fixture
def mock_requests():
    """Mock requests for HTTP calls."""
    with pytest.mock.patch('requests.Session') as mock:
        yield mock