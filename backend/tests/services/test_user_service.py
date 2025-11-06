import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from app.services.user import UserService
from app.schemas import UserUpdate


class TestUserService:
    def setup_method(self):
        self.db = MagicMock()
        self.user_service = UserService(self.db)

    def test_get_user_by_id_found(self):
        """Test getting user by ID when user exists"""
        # Arrange
        user_id = 1
        mock_user = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = mock_user

        # Act
        result = self.user_service.get_user_by_id(user_id)

        # Assert
        assert result == mock_user
        self.db.query.assert_called_once()
        self.db.query.return_value.filter.assert_called_once()

    def test_get_user_by_id_not_found(self):
        """Test getting user by ID when user doesn't exist"""
        # Arrange
        user_id = 1
        self.db.query.return_value.filter.return_value.first.return_value = None

        # Act
        result = self.user_service.get_user_by_id(user_id)

        # Assert
        assert result is None

    def test_get_user_by_auth_id_found(self):
        """Test getting user by auth provider ID when user exists"""
        # Arrange
        auth_id = "user_123"
        mock_user = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = mock_user

        # Act
        result = self.user_service.get_user_by_auth_id(auth_id)

        # Assert
        assert result == mock_user

    def test_get_user_by_auth_id_not_found(self):
        """Test getting user by auth provider ID when user doesn't exist"""
        # Arrange
        auth_id = "user_123"
        self.db.query.return_value.filter.return_value.first.return_value = None

        # Act
        result = self.user_service.get_user_by_auth_id(auth_id)

        # Assert
        assert result is None

    def test_get_user_by_email_found(self):
        """Test getting user by email when user exists"""
        # Arrange
        email = "test@example.com"
        mock_user = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = mock_user

        # Act
        result = self.user_service.get_user_by_email(email)

        # Assert
        assert result == mock_user

    def test_get_user_by_email_not_found(self):
        """Test getting user by email when user doesn't exist"""
        # Arrange
        email = "test@example.com"
        self.db.query.return_value.filter.return_value.first.return_value = None

        # Act
        result = self.user_service.get_user_by_email(email)

        # Assert
        assert result is None

    def test_get_or_create_user_existing_user_no_update(self):
        """Test get_or_create_user when user exists and no update needed"""
        # Arrange
        user_data = {
            "auth_provider_id": "user_123",
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe"
        }
        mock_user = MagicMock()
        mock_user.first_name = "John"
        mock_user.last_name = "Doe"

        with patch.object(self.user_service, 'get_user_by_auth_id', return_value=mock_user):
            # Act
            result = self.user_service.get_or_create_user(user_data)

            # Assert
            assert result == mock_user
            self.db.commit.assert_not_called()

    def test_get_or_create_user_existing_user_with_update(self):
        """Test get_or_create_user when user exists and needs update"""
        # Arrange
        user_data = {
            "auth_provider_id": "user_123",
            "email": "test@example.com",
            "first_name": "Jane",
            "last_name": "Smith"
        }
        mock_user = MagicMock()
        mock_user.first_name = "John"
        mock_user.last_name = "Doe"

        with patch.object(self.user_service, 'get_user_by_auth_id', return_value=mock_user):
            # Act
            result = self.user_service.get_or_create_user(user_data)

            # Assert
            assert result == mock_user
            assert mock_user.first_name == "Jane"
            assert mock_user.last_name == "Smith"
            self.db.commit.assert_called_once()
            self.db.refresh.assert_called_once_with(mock_user)

    def test_get_or_create_user_new_user(self):
        """Test get_or_create_user when creating new user"""
        # Arrange
        user_data = {
            "auth_provider_id": "user_123",
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe"
        }
        mock_user = MagicMock()

        with patch.object(self.user_service, 'get_user_by_auth_id', return_value=None), \
             patch('app.services.user.User', return_value=mock_user):
            # Act
            result = self.user_service.get_or_create_user(user_data)

            # Assert
            assert result == mock_user
            self.db.add.assert_called_once_with(mock_user)
            self.db.commit.assert_called_once()
            self.db.refresh.assert_called_once_with(mock_user)

    def test_update_user_success(self):
        """Test successful user update"""
        # Arrange
        user_id = 1
        user_update = UserUpdate(first_name="Jane", last_name="Smith")
        mock_user = MagicMock()

        with patch.object(self.user_service, 'get_user_by_id', return_value=mock_user):
            # Act
            result = self.user_service.update_user(user_id, user_update)

            # Assert
            assert result == mock_user
            assert mock_user.first_name == "Jane"
            assert mock_user.last_name == "Smith"
            self.db.commit.assert_called_once()
            self.db.refresh.assert_called_once_with(mock_user)

    def test_update_user_not_found(self):
        """Test updating user that doesn't exist"""
        # Arrange
        user_id = 1
        user_update = UserUpdate(first_name="Jane")

        with patch.object(self.user_service, 'get_user_by_id', return_value=None):
            # Act & Assert
            with pytest.raises(ValueError) as exc_info:
                self.user_service.update_user(user_id, user_update)

            assert "User not found" in str(exc_info.value)

    @patch("app.services.user.datetime")
    def test_handle_subscription_created_existing_user(self, mock_datetime):
        """Test subscription creation webhook for existing user"""
        # Arrange
        webhook_data = {
            "email": "test@example.com",
            "subscription_id": "sub_123",
            "product_id": "prod_456",
            "customer_id": "cus_789",
            "next_payment_date": "2024-12-01T00:00:00Z"
        }

        mock_user = MagicMock()
        mock_product = MagicMock()
        mock_product.subscription_tier = "pro"
        mock_product.id = 1

        mock_datetime.fromisoformat.return_value = datetime(2024, 12, 1)

        with patch.object(self.user_service, 'get_user_by_email', return_value=mock_user), \
             patch.object(self.user_service, 'get_or_create_user') as mock_get_or_create:
            self.db.query.return_value.filter.return_value.first.return_value = mock_product

            # Act
            self.user_service.handle_subscription_created(webhook_data)

            # Assert
            mock_get_or_create.assert_not_called()
            assert mock_user.subscription_tier == "pro"
            assert mock_user.paddle_customer_id == "cus_789"
            self.db.add.assert_called_once()
            self.db.commit.assert_called_once()

    @patch("app.services.user.datetime")
    def test_handle_subscription_created_new_user(self, mock_datetime):
        """Test subscription creation webhook for new user"""
        # Arrange
        webhook_data = {
            "email": "test@example.com",
            "subscription_id": "sub_123",
            "product_id": "prod_456",
            "customer_id": "cus_789",
            "next_payment_date": "2024-12-01T00:00:00Z"
        }

        mock_user = MagicMock()
        mock_product = MagicMock()
        mock_product.subscription_tier = "pro"
        mock_product.id = 1

        mock_datetime.fromisoformat.return_value = datetime(2024, 12, 1)

        with patch.object(self.user_service, 'get_user_by_email', return_value=None), \
             patch.object(self.user_service, 'get_or_create_user', return_value=mock_user):
            self.db.query.return_value.filter.return_value.first.return_value = mock_product

            # Act
            self.user_service.handle_subscription_created(webhook_data)

            # Assert
            # Note: get_or_create_user is mocked, so we can't assert its call directly
            assert mock_user.subscription_tier == "pro"
            assert mock_user.paddle_customer_id == "cus_789"
            self.db.add.assert_called_once()
            self.db.commit.assert_called_once()

    def test_handle_subscription_payment_success(self):
        """Test successful subscription payment handling"""
        # Arrange
        webhook_data = {"subscription_id": "sub_123"}

        mock_subscription = MagicMock()
        mock_user = MagicMock()
        mock_subscription.user = mock_user

        self.db.query.return_value.filter.return_value.first.return_value = mock_subscription

        # Act
        self.user_service.handle_subscription_payment(webhook_data)

        # Assert
        assert mock_subscription.status == "active"
        assert mock_user.monthly_credits_used == 0
        self.db.commit.assert_called_once()

    def test_handle_subscription_payment_not_found(self):
        """Test subscription payment handling when subscription not found"""
        # Arrange
        webhook_data = {"subscription_id": "sub_123"}

        self.db.query.return_value.filter.return_value.first.return_value = None

        # Act
        self.user_service.handle_subscription_payment(webhook_data)

        # Assert
        self.db.commit.assert_not_called()

    @patch("app.services.user.datetime")
    def test_handle_subscription_cancelled_success(self, mock_datetime):
        """Test successful subscription cancellation handling"""
        # Arrange
        webhook_data = {"subscription_id": "sub_123"}

        mock_subscription = MagicMock()
        mock_user = MagicMock()
        mock_subscription.user = mock_user
        mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0)

        self.db.query.return_value.filter.return_value.first.return_value = mock_subscription

        # Act
        self.user_service.handle_subscription_cancelled(webhook_data)

        # Assert
        assert mock_subscription.status == "cancelled"
        assert mock_subscription.cancelled_at == datetime(2024, 1, 1, 12, 0, 0)
        assert mock_user.subscription_tier == "free"
        self.db.commit.assert_called_once()

    def test_handle_subscription_cancelled_not_found(self):
        """Test subscription cancellation handling when subscription not found"""
        # Arrange
        webhook_data = {"subscription_id": "sub_123"}

        self.db.query.return_value.filter.return_value.first.return_value = None

        # Act
        self.user_service.handle_subscription_cancelled(webhook_data)

        # Assert
        self.db.commit.assert_not_called()

    def test_handle_payment_succeeded_existing_user(self):
        """Test one-time payment handling for existing user"""
        # Arrange
        webhook_data = {
            "email": "test@example.com",
            "product_id": "prod_456",
            "checkout_id": "checkout_123",
            "sale_gross": "29.99"
        }

        mock_user = MagicMock()
        mock_user.one_time_credits = 5
        mock_product = MagicMock()
        mock_product.credits_included = 10
        mock_product.id = 1

        with patch.object(self.user_service, 'get_user_by_email', return_value=mock_user), \
             patch.object(self.user_service, 'get_or_create_user') as mock_get_or_create:
            self.db.query.return_value.filter.return_value.first.return_value = mock_product

            # Act
            self.user_service.handle_payment_succeeded(webhook_data)

            # Assert
            mock_get_or_create.assert_not_called()
            assert mock_user.one_time_credits == 15  # 5 + 10
            self.db.add.assert_called_once()
            self.db.commit.assert_called_once()

    def test_handle_payment_succeeded_new_user(self):
        """Test one-time payment handling for new user"""
        # Arrange
        webhook_data = {
            "email": "test@example.com",
            "product_id": "prod_456",
            "checkout_id": "checkout_123",
            "sale_gross": "29.99"
        }

        mock_user = MagicMock()
        mock_user.one_time_credits = 0
        mock_product = MagicMock()
        mock_product.credits_included = 10
        mock_product.id = 1

        with patch.object(self.user_service, 'get_user_by_email', return_value=None), \
             patch.object(self.user_service, 'get_or_create_user', return_value=mock_user):
            self.db.query.return_value.filter.return_value.first.return_value = mock_product

            # Act
            self.user_service.handle_payment_succeeded(webhook_data)

            # Assert
            # Note: get_or_create_user is mocked, so we can't assert its call directly
            assert mock_user.one_time_credits == 10
            self.db.add.assert_called_once()
            self.db.commit.assert_called_once()