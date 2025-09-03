import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from src import models
from src.main import app


class TestAuthEndpoints:
    """Test authentication endpoints."""

    def test_register_success(self, client, db_session):
        """Test successful user registration."""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "testpass123"
        }

        response = client.post("/auth/register", json=user_data)

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "id" in data
        assert "hashed_password" not in data  # Should not return password

    def test_register_duplicate_username(self, client, sample_user):
        """Test registration with duplicate username."""
        user_data = {
            "username": "testuser",  # Same as sample_user
            "email": "different@example.com",
            "password": "testpass123"
        }

        response = client.post("/auth/register", json=user_data)

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_register_duplicate_email(self, client, sample_user):
        """Test registration with duplicate email."""
        user_data = {
            "username": "differentuser",
            "email": "test@example.com",  # Same as sample_user
            "password": "testpass123"
        }

        response = client.post("/auth/register", json=user_data)

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_login_success(self, client, sample_user, db_session):
        """Test successful login."""
        # Set password for sample user
        sample_user.hashed_password = "hashedpassword123"
        db_session.commit()

        # Mock password verification
        with patch('src.auth.verify_password', return_value=True):
            login_data = {
                "username": "testuser",
                "password": "testpass123"
            }

            response = client.post("/auth/login", json=login_data)

            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        login_data = {
            "username": "nonexistent",
            "password": "wrongpass"
        }

        response = client.post("/auth/login", json=login_data)

        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    def test_logout(self, client):
        """Test logout endpoint."""
        response = client.post("/auth/logout")

        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"

    def test_get_current_user_authenticated(self, client, auth_headers):
        """Test getting current user when authenticated."""
        response = client.get("/users/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"

    def test_get_current_user_unauthenticated(self, client):
        """Test getting current user when not authenticated."""
        response = client.get("/users/me")

        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestShoppingListEndpoints:
    """Test shopping list endpoints."""

    def test_get_shopping_lists_authenticated(self, client, auth_headers, sample_user, db_session):
        """Test getting shopping lists when authenticated."""
        # Create a shopping list for the user
        shopping_list = models.ShoppingList(
            title="Test List",
            description="Test description",
            user_id=sample_user.id
        )
        db_session.add(shopping_list)
        db_session.commit()

        response = client.get("/lists", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Test List"
        assert data[0]["description"] == "Test description"

    def test_get_shopping_lists_unauthenticated(self, client):
        """Test getting shopping lists when not authenticated."""
        response = client.get("/lists")

        assert response.status_code == 401

    def test_create_shopping_list_success(self, client, auth_headers, sample_user):
        """Test creating a shopping list successfully."""
        list_data = {
            "title": "New Shopping List",
            "description": "My new list"
        }

        response = client.post("/lists", json=list_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Shopping List"
        assert data["description"] == "My new list"
        assert data["user_id"] == sample_user.id

    def test_create_shopping_list_unauthenticated(self, client):
        """Test creating shopping list when not authenticated."""
        list_data = {
            "title": "New List",
            "description": "Test"
        }

        response = client.post("/lists", json=list_data)

        assert response.status_code == 401

    def test_get_shopping_list_by_id_success(self, client, auth_headers, sample_user, db_session):
        """Test getting a specific shopping list by ID."""
        shopping_list = models.ShoppingList(
            title="Specific List",
            user_id=sample_user.id
        )
        db_session.add(shopping_list)
        db_session.commit()

        response = client.get(f"/lists/{shopping_list.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Specific List"
        assert data["id"] == shopping_list.id

    def test_get_shopping_list_not_found(self, client, auth_headers):
        """Test getting non-existent shopping list."""
        response = client.get("/lists/999", headers=auth_headers)

        assert response.status_code == 404
        assert "Shopping list not found" in response.json()["detail"]

    def test_get_shopping_list_wrong_user(self, client, auth_headers, db_session):
        """Test getting shopping list that belongs to another user."""
        # Create another user
        other_user = models.User(
            username="otheruser",
            email="other@example.com",
            hashed_password="hashed123"
        )
        db_session.add(other_user)
        db_session.commit()

        # Create shopping list for other user
        shopping_list = models.ShoppingList(
            title="Other User's List",
            user_id=other_user.id
        )
        db_session.add(shopping_list)
        db_session.commit()

        response = client.get(f"/lists/{shopping_list.id}", headers=auth_headers)

        assert response.status_code == 404
        assert "Shopping list not found" in response.json()["detail"]

    def test_update_shopping_list_success(self, client, auth_headers, sample_user, db_session):
        """Test updating a shopping list successfully."""
        shopping_list = models.ShoppingList(
            title="Original Title",
            description="Original description",
            user_id=sample_user.id
        )
        db_session.add(shopping_list)
        db_session.commit()

        update_data = {
            "title": "Updated Title",
            "description": "Updated description"
        }

        response = client.put(f"/lists/{shopping_list.id}", json=update_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["description"] == "Updated description"

    def test_delete_shopping_list_success(self, client, auth_headers, sample_user, db_session):
        """Test deleting a shopping list successfully."""
        shopping_list = models.ShoppingList(
            title="List to Delete",
            user_id=sample_user.id
        )
        db_session.add(shopping_list)
        db_session.commit()

        response = client.delete(f"/lists/{shopping_list.id}", headers=auth_headers)

        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        # Verify it's actually deleted
        response = client.get(f"/lists/{shopping_list.id}", headers=auth_headers)
        assert response.status_code == 404