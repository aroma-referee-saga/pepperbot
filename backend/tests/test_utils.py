"""
Test utilities and helper functions for PepperBot backend tests.
"""

import random
import string
from typing import Dict, Any, Optional
from faker import Faker

from src import models
from sqlalchemy.orm import Session

fake = Faker()


def create_test_user(
    db: Session,
    username: Optional[str] = None,
    email: Optional[str] = None,
    password: Optional[str] = None,
    is_active: bool = True
) -> models.User:
    """Create a test user with default or provided values."""
    from src.auth import get_password_hash

    user_data = {
        "username": username or fake.user_name(),
        "email": email or fake.email(),
        "hashed_password": get_password_hash(password or fake.password()),
        "is_active": is_active
    }

    user = models.User(**user_data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_test_shopping_list(
    db: Session,
    user_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None
) -> models.ShoppingList:
    """Create a test shopping list."""
    list_data = {
        "title": title or fake.sentence(nb_words=3),
        "description": description or fake.text(max_nb_chars=100),
        "user_id": user_id
    }

    shopping_list = models.ShoppingList(**list_data)
    db.add(shopping_list)
    db.commit()
    db.refresh(shopping_list)
    return shopping_list


def create_test_list_item(
    db: Session,
    shopping_list_id: int,
    name: Optional[str] = None,
    quantity: Optional[float] = None,
    unit: Optional[str] = None,
    is_completed: bool = False
) -> models.ListItem:
    """Create a test list item."""
    item_data = {
        "name": name or fake.word().capitalize(),
        "quantity": quantity or random.uniform(0.5, 10.0),
        "unit": unit or random.choice(["kg", "pcs", "liters", "cups", None]),
        "is_completed": is_completed,
        "shopping_list_id": shopping_list_id
    }

    item = models.ListItem(**item_data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def create_test_discount(
    db: Session,
    title: Optional[str] = None,
    store: Optional[str] = None,
    original_price: Optional[float] = None,
    discount_price: Optional[float] = None,
    discount_percentage: Optional[float] = None,
    url: Optional[str] = None
) -> models.Discount:
    """Create a test discount."""
    discount_data = {
        "title": title or fake.sentence(nb_words=4),
        "description": fake.text(max_nb_chars=200),
        "store": store or fake.company(),
        "original_price": original_price or random.uniform(50, 1000),
        "discount_price": discount_price or random.uniform(20, 800),
        "discount_percentage": discount_percentage or random.uniform(5, 50),
        "url": url or fake.url(),
        "image_url": fake.image_url()
    }

    discount = models.Discount(**discount_data)
    db.add(discount)
    db.commit()
    db.refresh(discount)
    return discount


def create_test_filter(
    db: Session,
    user_id: int,
    name: Optional[str] = None,
    criteria: Optional[str] = None,
    is_active: bool = True
) -> models.Filter:
    """Create a test filter."""
    filter_data = {
        "name": name or fake.sentence(nb_words=2),
        "criteria": criteria or '{"store": "Amazon", "min_discount": 20}',
        "is_active": is_active,
        "user_id": user_id
    }

    filter_obj = models.Filter(**filter_data)
    db.add(filter_obj)
    db.commit()
    db.refresh(filter_obj)
    return filter_obj


def create_test_notification(
    db: Session,
    user_id: int,
    title: Optional[str] = None,
    message: Optional[str] = None,
    type_: Optional[str] = None,
    discount_id: Optional[int] = None,
    is_read: bool = False
) -> models.Notification:
    """Create a test notification."""
    notification_data = {
        "title": title or fake.sentence(nb_words=3),
        "message": message or fake.text(max_nb_chars=150),
        "type": type_ or random.choice(["discount", "reminder", "system"]),
        "is_read": is_read,
        "user_id": user_id,
        "discount_id": discount_id
    }

    notification = models.Notification(**notification_data)
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def create_test_telegram_user(
    db: Session,
    user_id: int,
    telegram_chat_id: Optional[str] = None,
    is_active: bool = True
) -> models.TelegramUser:
    """Create a test Telegram user link."""
    telegram_data = {
        "telegram_chat_id": telegram_chat_id or str(fake.random_int(min=100000, max=999999)),
        "user_id": user_id,
        "is_active": is_active
    }

    telegram_user = models.TelegramUser(**telegram_data)
    db.add(telegram_user)
    db.commit()
    db.refresh(telegram_user)
    return telegram_user


def generate_random_string(length: int = 10) -> str:
    """Generate a random string of specified length."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_random_email() -> str:
    """Generate a random email address."""
    return fake.email()


def generate_random_password() -> str:
    """Generate a random password."""
    return fake.password()


def create_auth_headers(user_id: int = 1) -> Dict[str, str]:
    """Create authentication headers for testing."""
    from src.auth import create_access_token

    token = create_access_token(data={"sub": f"testuser{user_id}"})
    return {"Authorization": f"Bearer {token}"}


def assert_model_fields(model, expected_fields: Dict[str, Any]):
    """Assert that a model has the expected field values."""
    for field, expected_value in expected_fields.items():
        assert hasattr(model, field), f"Model missing field: {field}"
        actual_value = getattr(model, field)
        assert actual_value == expected_value, f"Field {field}: expected {expected_value}, got {actual_value}"


def assert_api_response(response, expected_status: int = 200, expected_data: Optional[Dict] = None):
    """Assert API response has expected status and data."""
    assert response.status_code == expected_status

    if expected_data:
        response_data = response.json()
        for key, expected_value in expected_data.items():
            assert key in response_data, f"Response missing key: {key}"
            assert response_data[key] == expected_value


def cleanup_test_data(db: Session):
    """Clean up test data from database."""
    try:
        db.query(models.Notification).delete()
        db.query(models.ListItem).delete()
        db.query(models.ShoppingList).delete()
        db.query(models.Filter).delete()
        db.query(models.TelegramUser).delete()
        db.query(models.Discount).delete()
        db.query(models.User).delete()
        db.commit()
    except Exception as e:
        db.rollback()
        raise e


class MockResponse:
    """Mock HTTP response for testing."""

    def __init__(self, json_data: Optional[Dict] = None, status_code: int = 200, text: str = ""):
        self.json_data = json_data or {}
        self.status_code = status_code
        self.text = text

    def json(self):
        return self.json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


def mock_httpx_response(json_data: Optional[Dict] = None, status_code: int = 200):
    """Create a mock httpx response."""
    return MockResponse(json_data, status_code)


def mock_requests_response(text: str = "", status_code: int = 200):
    """Create a mock requests response."""
    response = MockResponse(None, status_code, text)
    response.raise_for_status = lambda: None if status_code < 400 else Exception(f"HTTP {status_code}")
    return response