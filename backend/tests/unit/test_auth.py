import pytest
from unittest.mock import MagicMock, patch
from datetime import timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session

from src import auth, models
from config.settings import settings


class TestPasswordHashing:
    """Test password hashing functions."""

    def test_verify_password_correct(self):
        """Test verifying correct password."""
        plain_password = "testpassword123"
        hashed = auth.get_password_hash(plain_password)

        assert auth.verify_password(plain_password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        plain_password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = auth.get_password_hash(plain_password)

        assert auth.verify_password(wrong_password, hashed) is False

    def test_get_password_hash_unique(self):
        """Test that password hashes are unique for same password."""
        password = "testpassword"
        hash1 = auth.get_password_hash(password)
        hash2 = auth.get_password_hash(password)

        # Hashes should be different due to salt
        assert hash1 != hash2
        # But both should verify the same password
        assert auth.verify_password(password, hash1) is True
        assert auth.verify_password(password, hash2) is True


class TestJWTToken:
    """Test JWT token creation and validation."""

    def test_create_access_token(self):
        """Test creating access token."""
        data = {"sub": "testuser"}
        token = auth.create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_expiry(self):
        """Test creating access token with custom expiry."""
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=30)
        token = auth.create_access_token(data, expires_delta)

        assert isinstance(token, str)

    def test_get_current_user_from_token_valid(self, db_session, sample_user):
        """Test getting user from valid token."""
        # Create token for sample user
        token = auth.create_access_token(data={"sub": sample_user.username})

        # Get user from token
        user = auth.get_current_user_from_token(token, db_session)

        assert user.id == sample_user.id
        assert user.username == sample_user.username

    def test_get_current_user_from_token_invalid_user(self, db_session):
        """Test getting user from token with non-existent user."""
        token = auth.create_access_token(data={"sub": "nonexistentuser"})

        with pytest.raises(HTTPException) as exc_info:
            auth.get_current_user_from_token(token, db_session)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)

    def test_get_current_user_from_token_invalid_token(self, db_session):
        """Test getting user from invalid token."""
        invalid_token = "invalid.jwt.token"

        with pytest.raises(HTTPException) as exc_info:
            auth.get_current_user_from_token(invalid_token, db_session)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)

    def test_get_current_user_from_token_expired(self, db_session, sample_user):
        """Test getting user from expired token."""
        # Create expired token
        expired_delta = timedelta(minutes=-1)
        expired_token = auth.create_access_token(
            data={"sub": sample_user.username},
            expires_delta=expired_delta
        )

        with pytest.raises(HTTPException) as exc_info:
            auth.get_current_user_from_token(expired_token, db_session)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)


class TestUserAuthentication:
    """Test user authentication functions."""

    def test_authenticate_user_success(self, db_session, sample_user):
        """Test successful user authentication."""
        # Update user with plain password hash for testing
        sample_user.hashed_password = auth.get_password_hash("testpass")
        db_session.commit()

        user = auth.authenticate_user(db_session, "testuser", "testpass")

        assert user is not None
        assert user.username == "testuser"

    def test_authenticate_user_wrong_password(self, db_session, sample_user):
        """Test authentication with wrong password."""
        sample_user.hashed_password = auth.get_password_hash("correctpass")
        db_session.commit()

        user = auth.authenticate_user(db_session, "testuser", "wrongpass")

        assert user is False

    def test_authenticate_user_nonexistent_user(self, db_session):
        """Test authentication with non-existent user."""
        user = auth.authenticate_user(db_session, "nonexistent", "password")

        assert user is False


class TestCurrentUser:
    """Test getting current user from request."""

    def test_get_current_active_user_success(self, sample_user):
        """Test getting active user."""
        user = auth.get_current_active_user(sample_user)

        assert user.id == sample_user.id
        assert user.is_active is True

    def test_get_current_active_user_inactive(self, sample_user):
        """Test getting inactive user raises exception."""
        sample_user.is_active = False

        with pytest.raises(HTTPException) as exc_info:
            auth.get_current_active_user(sample_user)

        assert exc_info.value.status_code == 400
        assert "Inactive user" in str(exc_info.value.detail)

    @patch('src.auth.security')
    def test_get_current_user_cookie_success(self, mock_security, db_session, sample_user):
        """Test getting user from cookie."""
        # Mock request with cookie
        mock_request = MagicMock()
        mock_request.cookies = {"access_token": "Bearer testtoken"}
        mock_request.headers = {}

        # Mock token validation
        with patch.object(auth, 'get_current_user_from_token', return_value=sample_user):
            user = auth.get_current_user(mock_request, db_session)

        assert user.id == sample_user.id

    @patch('src.auth.security')
    def test_get_current_user_header_success(self, mock_security, db_session, sample_user):
        """Test getting user from Authorization header."""
        # Mock request without cookie but with header
        mock_request = MagicMock()
        mock_request.cookies = {}
        mock_request.headers = {"Authorization": "Bearer testtoken"}

        # Mock security scheme
        mock_credentials = MagicMock()
        mock_credentials.credentials = "testtoken"
        mock_security.return_value = mock_credentials

        # Mock token validation
        with patch.object(auth, 'get_current_user_from_token', return_value=sample_user):
            user = auth.get_current_user(mock_request, db_session)

        assert user.id == sample_user.id

    def test_get_current_user_no_token(self, db_session):
        """Test getting user without token raises exception."""
        mock_request = MagicMock()
        mock_request.cookies = {}
        mock_request.headers = {}

        with pytest.raises(HTTPException) as exc_info:
            auth.get_current_user(mock_request, db_session)

        assert exc_info.value.status_code == 401
        assert "Not authenticated" in str(exc_info.value.detail)