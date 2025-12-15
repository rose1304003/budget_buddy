"""
Test configuration and fixtures for backend tests.

This file provides shared fixtures and utilities for testing.
Copy this to: backend/tests/conftest.py
"""

import pytest
import hashlib
import hmac
import json
import time
import os
import sys
import pytest

# Rest of your conftest.py stays the same...
from sqlmodel import Session, SQLModel, create_engine
from fastapi.testclient import TestClient
# ... etc
from app.settings import settings as app_settings
from typing import Dict, Generator
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.db import get_session
from app.models import User, Category, Transaction



# Set test environment variables BEFORE importing app
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test_token_123456:ABCdef")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")
os.environ.setdefault("APP_NAME", "Teacher Budget Buddy Test")

# Test database setup
@pytest.fixture(name="session")
def session_fixture() -> Generator[Session, None, None]:
    """
    Create a fresh test database session for each test.
    Uses in-memory SQLite for speed.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session) -> TestClient:
    """
    Create a test client with overridden database session.
    """
    def get_session_override():
        return session
    
    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def test_bot_token() -> str:
    """Return a consistent test bot token"""
    return "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"


@pytest.fixture
def test_user(session: Session) -> User:
    """Create a test user"""
    user = User(
        tg_user_id=123456,
        first_name="Test",
        last_name="User",
        username="testuser",
        language_code="en"
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def test_category(session: Session, test_user: User) -> Category:
    """Create a test category"""
    category = Category(
        user_id=test_user.id,
        name="Test Category",
        kind="expense",
        color="#22d3ee",
        icon="shopping-cart",
        is_active=True
    )
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


@pytest.fixture
def test_transaction(session: Session, test_user: User, test_category: Category) -> Transaction:
    """Create a test transaction"""
    transaction = Transaction(
        user_id=test_user.id,
        category_id=test_category.id,
        type="expense",
        amount=50000,
        note="Test transaction"
    )
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    return transaction


def create_test_init_data(
    user_id: int,
    first_name: str = "Test",
    last_name: str = "User",
    username: str = "testuser",
    bot_token: str = "8482204594:AAG73jMBTN6tnI1go5Y79qJEKUkJXRQixos",
    auth_date_offset: int = 0,
) -> str:
    """
    Generate valid Telegram initData for testing.
    
    Args:
        user_id: Telegram user ID
        first_name: User's first name
        last_name: User's last name
        username: User's username
        bot_token: Bot token for signature generation
        auth_date_offset: Offset from current time in seconds (negative for past)
    
    Returns:
        Valid initData string that will pass verification
    """
    auth_date = int(time.time()) + auth_date_offset
    
    user_data = {
        "id": user_id,
        "first_name": first_name,
        "last_name": last_name,
        "username": username,
        "language_code": "en",
    }
    
    data: Dict[str, str] = {
        "auth_date": str(auth_date),
        "user": json.dumps(user_data),
    }
    
    # Create data_check_string
    pairs = [f"{k}={v}" for k, v in sorted(data.items())]
    data_check_string = "\n".join(pairs)
    
    # Compute hash using bot token
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    hash_value = hmac.new(
        secret_key, 
        data_check_string.encode(), 
        hashlib.sha256
    ).hexdigest()
    
    # Build init_data string
    data["hash"] = hash_value
    return "&".join(f"{k}={v}" for k, v in data.items())


@pytest.fixture
def auth_headers() -> Dict[str, str]:
    """
    Generate authentication headers for test requests.
    """
    init_data = create_test_init_data(
        user_id=123456,
        first_name="Test",
        last_name="User",
        username="testuser",
        bot_token=app_settings.telegram_bot_token,  # Use real bot token
    )
    
    return {"X-TG-Init-Data": init_data}


@pytest.fixture(autouse=True)
def reset_cache():
    """
    Reset any caches between tests.
    Add this if you implement caching.
    """
    # Example: redis_client.flushdb() if redis is available
    pass


# Helper functions
def assert_response_ok(response, expected_status: int = 200):
    """Assert that response is successful"""
    assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}: {response.text}"


def assert_valid_transaction(data: dict):
    """Assert that transaction data is valid"""
    assert "id" in data
    assert "type" in data
    assert data["type"] in ["expense", "income"]
    assert "amount" in data
    assert isinstance(data["amount"], int)
    assert data["amount"] > 0


def assert_valid_category(data: dict):
    """Assert that category data is valid"""
    assert "id" in data
    assert "name" in data
    assert "kind" in data
    assert data["kind"] in ["expense", "income", "debt"]
    assert "color" in data
    assert data["color"].startswith("#")
