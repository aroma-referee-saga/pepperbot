import pytest
from datetime import datetime
from src import models


class TestUserModel:
    """Test cases for User model."""

    def test_user_creation(self, db_session):
        """Test creating a user."""
        user = models.User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed123"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.hashed_password == "hashed123"
        assert user.is_active is True
        assert isinstance(user.created_at, datetime)

    def test_user_relationships(self, db_session):
        """Test user relationships."""
        user = models.User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed123"
        )
        db_session.add(user)
        db_session.commit()

        # Test shopping lists relationship
        shopping_list = models.ShoppingList(
            title="Test List",
            user_id=user.id
        )
        db_session.add(shopping_list)
        db_session.commit()

        assert len(user.shopping_lists) == 1
        assert user.shopping_lists[0].title == "Test List"

    def test_user_unique_constraints(self, db_session):
        """Test unique constraints on username and email."""
        user1 = models.User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed123"
        )
        db_session.add(user1)
        db_session.commit()

        # Try to create user with same username
        user2 = models.User(
            username="testuser",
            email="different@example.com",
            hashed_password="hashed456"
        )
        db_session.add(user2)

        with pytest.raises(Exception):  # Should raise IntegrityError
            db_session.commit()


class TestShoppingListModel:
    """Test cases for ShoppingList model."""

    def test_shopping_list_creation(self, db_session, sample_user):
        """Test creating a shopping list."""
        shopping_list = models.ShoppingList(
            title="Groceries",
            description="Weekly groceries",
            user_id=sample_user.id
        )
        db_session.add(shopping_list)
        db_session.commit()
        db_session.refresh(shopping_list)

        assert shopping_list.id is not None
        assert shopping_list.title == "Groceries"
        assert shopping_list.description == "Weekly groceries"
        assert shopping_list.user_id == sample_user.id
        assert isinstance(shopping_list.created_at, datetime)
        assert isinstance(shopping_list.updated_at, datetime)

    def test_shopping_list_items_relationship(self, db_session, sample_user):
        """Test shopping list items relationship."""
        shopping_list = models.ShoppingList(
            title="Test List",
            user_id=sample_user.id
        )
        db_session.add(shopping_list)
        db_session.commit()

        item = models.ListItem(
            name="Milk",
            quantity=2.0,
            unit="liters",
            shopping_list_id=shopping_list.id
        )
        db_session.add(item)
        db_session.commit()

        assert len(shopping_list.items) == 1
        assert shopping_list.items[0].name == "Milk"


class TestListItemModel:
    """Test cases for ListItem model."""

    def test_list_item_creation(self, db_session, sample_user):
        """Test creating a list item."""
        shopping_list = models.ShoppingList(
            title="Test List",
            user_id=sample_user.id
        )
        db_session.add(shopping_list)
        db_session.commit()

        item = models.ListItem(
            name="Bread",
            quantity=1.0,
            unit="loaf",
            shopping_list_id=shopping_list.id
        )
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)

        assert item.id is not None
        assert item.name == "Bread"
        assert item.quantity == 1.0
        assert item.unit == "loaf"
        assert item.is_completed is False
        assert item.shopping_list_id == shopping_list.id
        assert isinstance(item.created_at, datetime)
        assert isinstance(item.updated_at, datetime)

    def test_list_item_defaults(self, db_session, sample_user):
        """Test list item default values."""
        shopping_list = models.ShoppingList(
            title="Test List",
            user_id=sample_user.id
        )
        db_session.add(shopping_list)
        db_session.commit()

        item = models.ListItem(
            name="Apples",
            shopping_list_id=shopping_list.id
        )
        db_session.add(item)
        db_session.commit()

        assert item.quantity == 1.0
        assert item.unit is None
        assert item.is_completed is False


class TestFilterModel:
    """Test cases for Filter model."""

    def test_filter_creation(self, db_session, sample_user):
        """Test creating a filter."""
        filter_obj = models.Filter(
            name="Electronics Filter",
            criteria='{"store": "Amazon", "min_discount": 20}',
            user_id=sample_user.id
        )
        db_session.add(filter_obj)
        db_session.commit()
        db_session.refresh(filter_obj)

        assert filter_obj.id is not None
        assert filter_obj.name == "Electronics Filter"
        assert filter_obj.criteria == '{"store": "Amazon", "min_discount": 20}'
        assert filter_obj.is_active is True
        assert filter_obj.user_id == sample_user.id
        assert isinstance(filter_obj.created_at, datetime)


class TestDiscountModel:
    """Test cases for Discount model."""

    def test_discount_creation(self, db_session):
        """Test creating a discount."""
        discount = models.Discount(
            title="iPhone Discount",
            description="20% off iPhone",
            store="Apple Store",
            original_price=1000.0,
            discount_price=800.0,
            discount_percentage=20.0,
            url="https://example.com/iphone"
        )
        db_session.add(discount)
        db_session.commit()
        db_session.refresh(discount)

        assert discount.id is not None
        assert discount.title == "iPhone Discount"
        assert discount.description == "20% off iPhone"
        assert discount.store == "Apple Store"
        assert discount.original_price == 1000.0
        assert discount.discount_price == 800.0
        assert discount.discount_percentage == 20.0
        assert discount.url == "https://example.com/iphone"
        assert isinstance(discount.created_at, datetime)

    def test_discount_optional_fields(self, db_session):
        """Test discount with minimal required fields."""
        discount = models.Discount(
            title="Basic Discount",
            store="Test Store"
        )
        db_session.add(discount)
        db_session.commit()

        assert discount.original_price is None
        assert discount.discount_price is None
        assert discount.discount_percentage is None
        assert discount.description is None
        assert discount.url is None
        assert discount.image_url is None
        assert discount.valid_until is None


class TestNotificationModel:
    """Test cases for Notification model."""

    def test_notification_creation(self, db_session, sample_user, sample_discount):
        """Test creating a notification."""
        notification = models.Notification(
            title="New Discount Available",
            message="Check out this great deal!",
            type="discount",
            user_id=sample_user.id,
            discount_id=sample_discount.id
        )
        db_session.add(notification)
        db_session.commit()
        db_session.refresh(notification)

        assert notification.id is not None
        assert notification.title == "New Discount Available"
        assert notification.message == "Check out this great deal!"
        assert notification.type == "discount"
        assert notification.is_read is False
        assert notification.user_id == sample_user.id
        assert notification.discount_id == sample_discount.id
        assert isinstance(notification.created_at, datetime)


class TestTelegramUserModel:
    """Test cases for TelegramUser model."""

    def test_telegram_user_creation(self, db_session, sample_user):
        """Test creating a Telegram user link."""
        telegram_user = models.TelegramUser(
            telegram_chat_id="123456789",
            user_id=sample_user.id
        )
        db_session.add(telegram_user)
        db_session.commit()
        db_session.refresh(telegram_user)

        assert telegram_user.id is not None
        assert telegram_user.telegram_chat_id == "123456789"
        assert telegram_user.user_id == sample_user.id
        assert telegram_user.is_active is True
        assert isinstance(telegram_user.created_at, datetime)

    def test_telegram_user_unique_chat_id(self, db_session, sample_user):
        """Test unique constraint on telegram_chat_id."""
        telegram_user1 = models.TelegramUser(
            telegram_chat_id="123456789",
            user_id=sample_user.id
        )
        db_session.add(telegram_user1)
        db_session.commit()

        # Try to create another with same chat_id
        telegram_user2 = models.TelegramUser(
            telegram_chat_id="123456789",
            user_id=sample_user.id
        )
        db_session.add(telegram_user2)

        with pytest.raises(Exception):  # Should raise IntegrityError
            db_session.commit()