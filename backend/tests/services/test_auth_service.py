import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.services.auth import verify_clerk_token, get_current_user, get_optional_current_user
from app.schemas import User as UserSchema


class TestVerifyClerkToken:
    @patch("app.services.auth.settings")
    def test_verify_clerk_token_testing_mode_success(self, mock_settings):
        """Test token verification in testing mode with dev key"""
        # Arrange
        mock_settings.TESTING_MODE = True
        token = "dev-secret-key-for-testing-only"

        # Act
        result = verify_clerk_token(token)

        # Assert
        expected = {
            "auth_provider_id": "dev_user_123",
            "email": "dev@example.com",
            "first_name": "Dev",
            "last_name": "User"
        }
        assert result == expected

    @patch("app.services.auth.settings")
    def test_verify_clerk_token_testing_mode_wrong_token(self, mock_settings):
        """Test token verification in testing mode with wrong token"""
        # Arrange
        mock_settings.TESTING_MODE = True
        mock_settings.CLERK_PEM_PUBLIC_KEY = "public_key"
        mock_settings.CLERK_JWT_ISSUER = "issuer"
        mock_settings.CLERK_JWT_AUDIENCE = "audience"
        token = "wrong-token"

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            verify_clerk_token(token)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)

    @patch("app.services.auth.settings")
    def test_verify_clerk_token_missing_config(self, mock_settings):
        """Test token verification with missing Clerk configuration"""
        # Arrange
        mock_settings.TESTING_MODE = False
        mock_settings.CLERK_PEM_PUBLIC_KEY = None
        mock_settings.CLERK_JWT_ISSUER = "issuer"
        mock_settings.CLERK_JWT_AUDIENCE = "audience"
        token = "some-token"

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            verify_clerk_token(token)

        assert exc_info.value.status_code == 500
        assert "Clerk authentication not fully configured" in str(exc_info.value.detail)

    @patch("app.services.auth.jwt.decode")
    @patch("app.services.auth.settings")
    def test_verify_clerk_token_success(self, mock_settings, mock_jwt_decode):
        """Test successful token verification"""
        # Arrange
        mock_settings.TESTING_MODE = False
        mock_settings.CLERK_PEM_PUBLIC_KEY = "public_key"
        mock_settings.CLERK_JWT_ISSUER = "issuer"
        mock_settings.CLERK_JWT_AUDIENCE = "audience"

        mock_payload = {
            "sub": "user_123",
            "email_addresses": [{"email_address": "test@example.com"}],
            "given_name": "John",
            "family_name": "Doe"
        }
        mock_jwt_decode.return_value = mock_payload

        token = "valid-token"

        # Act
        result = verify_clerk_token(token)

        # Assert
        expected = {
            "auth_provider_id": "user_123",
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe"
        }
        assert result == expected

        mock_jwt_decode.assert_called_once_with(
            token,
            key="public_key",
            algorithms=["RS256"],
            audience="audience",
            issuer="issuer",
            options={"verify_signature": True, "verify_aud": True, "verify_iss": True}
        )

    @patch("app.services.auth.jwt.decode")
    @patch("app.services.auth.settings")
    def test_verify_clerk_token_no_email(self, mock_settings, mock_jwt_decode):
        """Test token verification with no email in payload"""
        # Arrange
        mock_settings.TESTING_MODE = False
        mock_settings.CLERK_PEM_PUBLIC_KEY = "public_key"
        mock_settings.CLERK_JWT_ISSUER = "issuer"
        mock_settings.CLERK_JWT_AUDIENCE = "audience"

        mock_payload = {
            "sub": "user_123",
            "given_name": "John",
            "family_name": "Doe"
        }
        mock_jwt_decode.return_value = mock_payload

        token = "valid-token"

        # Act
        result = verify_clerk_token(token)

        # Assert
        expected = {
            "auth_provider_id": "user_123",
            "email": None,
            "first_name": "John",
            "last_name": "Doe"
        }
        assert result == expected

    @patch("app.services.auth.jwt.decode")
    @patch("app.services.auth.settings")
    def test_verify_clerk_token_jwt_error(self, mock_settings, mock_jwt_decode):
        """Test token verification with JWT decode error"""
        # Arrange
        mock_settings.TESTING_MODE = False
        mock_settings.CLERK_PEM_PUBLIC_KEY = "public_key"
        mock_settings.CLERK_JWT_ISSUER = "issuer"
        mock_settings.CLERK_JWT_AUDIENCE = "audience"

        from jose import JWTError
        mock_jwt_decode.side_effect = JWTError("Invalid token")

        token = "invalid-token"

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            verify_clerk_token(token)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)


class TestGetCurrentUser:
    @patch("app.services.auth.settings")
    def test_get_current_user_testing_mode_success(self, mock_settings):
        """Test get_current_user in testing mode"""
        # Arrange
        mock_settings.TESTING_MODE = True
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="dev-secret-key-for-testing-only")
        db = MagicMock()

        # Act
        result = get_current_user(credentials, db)

        # Assert
        assert isinstance(result, UserSchema)
        assert result.id == 1
        assert result.auth_provider_id == "dev_user_123"
        assert result.email == "dev@example.com"

    @patch("app.services.auth.settings")
    @patch("app.services.auth.verify_clerk_token")
    @patch("app.services.auth.UserService")
    def test_get_current_user_success_existing_user(self, mock_user_service_class, mock_verify_token, mock_settings):
        """Test get_current_user with existing user"""
        # Arrange
        mock_settings.TESTING_MODE = False
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token")
        db = MagicMock()

        user_data = {
            "auth_provider_id": "user_123",
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe"
        }
        mock_verify_token.return_value = user_data

        mock_user_service = MagicMock()
        mock_user = MagicMock()
        mock_user_service.get_user_by_auth_id.return_value = mock_user
        mock_user_service_class.return_value = mock_user_service

        # Act
        result = get_current_user(credentials, db)

        # Assert
        assert result == mock_user
        mock_verify_token.assert_called_once_with("valid-token")
        mock_user_service.get_user_by_auth_id.assert_called_once_with("user_123")

    @patch("app.services.auth.settings")
    @patch("app.services.auth.verify_clerk_token")
    @patch("app.services.auth.UserService")
    def test_get_current_user_testing_mode_create_user(self, mock_user_service_class, mock_verify_token, mock_settings):
        """Test get_current_user in testing mode creating new user"""
        # Arrange
        mock_settings.TESTING_MODE = True
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="some-token")
        db = MagicMock()

        user_data = {
            "auth_provider_id": "user_123",
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe"
        }
        mock_verify_token.return_value = user_data

        mock_user_service = MagicMock()
        mock_user = MagicMock()
        mock_user_service.get_user_by_auth_id.return_value = None  # User doesn't exist
        mock_user_service.get_or_create_user.return_value = mock_user
        mock_user_service_class.return_value = mock_user_service

        # Act
        result = get_current_user(credentials, db)

        # Assert
        assert result == mock_user
        mock_user_service.get_or_create_user.assert_called_once_with(user_data)

    @patch("app.services.auth.settings")
    @patch("app.services.auth.verify_clerk_token")
    @patch("app.services.auth.UserService")
    def test_get_current_user_user_not_found(self, mock_user_service_class, mock_verify_token, mock_settings):
        """Test get_current_user when user doesn't exist and not in testing mode"""
        # Arrange
        mock_settings.TESTING_MODE = False
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token")
        db = MagicMock()

        user_data = {
            "auth_provider_id": "user_123",
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe"
        }
        mock_verify_token.return_value = user_data

        mock_user_service = MagicMock()
        mock_user_service.get_user_by_auth_id.return_value = None  # User doesn't exist
        mock_user_service_class.return_value = mock_user_service

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials, db)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)

    @patch("app.services.auth.settings")
    @patch("app.services.auth.verify_clerk_token")
    def test_get_current_user_invalid_token(self, mock_verify_token, mock_settings):
        """Test get_current_user with invalid token"""
        # Arrange
        mock_settings.TESTING_MODE = False
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid-token")
        db = MagicMock()

        from jose import JWTError
        mock_verify_token.side_effect = JWTError("Invalid token")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials, db)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)


class TestGetOptionalCurrentUser:
    def test_get_optional_current_user_no_credentials(self):
        """Test get_optional_current_user with no credentials"""
        # Arrange
        credentials = None
        db = MagicMock()

        # Act
        result = get_optional_current_user(credentials, db)

        # Assert
        assert result is None

    @patch("app.services.auth.verify_clerk_token")
    @patch("app.services.auth.UserService")
    def test_get_optional_current_user_success(self, mock_user_service_class, mock_verify_token):
        """Test get_optional_current_user with valid credentials"""
        # Arrange
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token")
        db = MagicMock()

        user_data = {
            "auth_provider_id": "user_123",
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe"
        }
        mock_verify_token.return_value = user_data

        mock_user_service = MagicMock()
        mock_user = MagicMock()
        mock_user_service.get_user_by_auth_id.return_value = mock_user
        mock_user_service_class.return_value = mock_user_service

        # Act
        result = get_optional_current_user(credentials, db)

        # Assert
        assert result == mock_user
        mock_verify_token.assert_called_once_with("valid-token")
        mock_user_service.get_user_by_auth_id.assert_called_once_with("user_123")

    @patch("app.services.auth.verify_clerk_token")
    @patch("app.services.auth.UserService")
    def test_get_optional_current_user_invalid_token(self, mock_user_service_class, mock_verify_token):
        """Test get_optional_current_user with invalid token"""
        # Arrange
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid-token")
        db = MagicMock()

        from jose import JWTError
        mock_verify_token.side_effect = JWTError("Invalid token")

        # Act
        result = get_optional_current_user(credentials, db)

        # Assert
        assert result is None