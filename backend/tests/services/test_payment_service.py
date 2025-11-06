import pytest
from unittest.mock import MagicMock, patch, mock_open
import json

from app.services.payment import PaymentService, PaddleCheckoutRequest


class TestPaymentService:
    def setup_method(self):
        with patch("app.services.payment.settings") as mock_settings:
            mock_settings.PADDLE_VENDOR_ID = "12345"
            mock_settings.PADDLE_VENDOR_AUTH_CODE = "auth_code"
            mock_settings.PADDLE_PUBLIC_KEY = "public_key"
            self.payment_service = PaymentService()

    @patch("app.services.payment.settings")
    def test_init(self, mock_settings):
        """Test PaymentService initialization"""
        # Arrange
        mock_settings.PADDLE_VENDOR_ID = "12345"
        mock_settings.PADDLE_VENDOR_AUTH_CODE = "auth_code"
        mock_settings.PADDLE_PUBLIC_KEY = "public_key"

        # Act
        service = PaymentService()

        # Assert
        assert service.vendor_id == "12345"
        assert service.vendor_auth_code == "auth_code"
        assert service.public_key == "public_key"
        assert service.api_endpoint == "https://vendors.paddle.com/api/2.0"
        assert service.sandbox_api_endpoint == "https://sandbox-vendors.paddle.com/api/2.0"

    @patch("app.services.payment.settings")
    def test_get_api_url_production(self, mock_settings):
        """Test _get_api_url in production environment"""
        # Arrange
        mock_settings.PADDLE_ENVIRONMENT = "production"

        # Act
        url = self.payment_service._get_api_url()

        # Assert
        assert url == "https://vendors.paddle.com/api/2.0"

    @patch("app.services.payment.settings")
    def test_get_api_url_sandbox(self, mock_settings):
        """Test _get_api_url in sandbox environment"""
        # Arrange
        mock_settings.PADDLE_ENVIRONMENT = "sandbox"

        # Act
        url = self.payment_service._get_api_url()

        # Assert
        assert url == "https://sandbox-vendors.paddle.com/api/2.0"

    @patch("app.services.payment.settings")
    def test_generate_checkout_url_testing_mode(self, mock_settings):
        """Test generate_checkout_url in testing mode"""
        # Arrange
        mock_settings.TESTING_MODE = True
        checkout_request = PaddleCheckoutRequest(
            product_id=123,
            customer_email="test@example.com"
        )

        # Act
        url = self.payment_service.generate_checkout_url(checkout_request)

        # Assert
        expected_url = "http://localhost:3000/mock-checkout?product_id=123&email=test@example.com"
        assert url == expected_url

    @patch("app.services.payment.settings")
    @patch("app.services.payment.requests.post")
    def test_generate_checkout_url_success(self, mock_requests_post, mock_settings):
        """Test successful checkout URL generation"""
        # Arrange
        mock_settings.TESTING_MODE = False
        mock_settings.PADDLE_ENVIRONMENT = "production"
        mock_settings.PADDLE_VENDOR_ID = "12345"
        mock_settings.PADDLE_VENDOR_AUTH_CODE = "auth_code"

        checkout_request = PaddleCheckoutRequest(
            product_id=123,
            customer_email="test@example.com",
            custom_message="Test message"
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "response": {"url": "https://checkout.paddle.com/checkout/abc123"}
        }
        mock_requests_post.return_value = mock_response

        # Act
        url = self.payment_service.generate_checkout_url(checkout_request)

        # Assert
        assert url == "https://checkout.paddle.com/checkout/abc123"

        # Verify the API call
        mock_requests_post.assert_called_once()
        call_args = mock_requests_post.call_args
        assert call_args[0][0] == "https://vendors.paddle.com/api/2.0/product/generate_pay_link"

        payload = call_args[1]["json"]
        assert payload["vendor_id"] == "12345"
        assert payload["vendor_auth_code"] == "auth_code"
        assert payload["product_id"] == 123
        assert payload["customer_email"] == "test@example.com"
        assert payload["custom_message"] == "Test message"
        assert payload["passthrough"] == '{"user_email": "test@example.com"}'

    @patch("app.services.payment.settings")
    @patch("app.services.payment.requests.post")
    def test_generate_checkout_url_api_error(self, mock_requests_post, mock_settings):
        """Test checkout URL generation with API error"""
        # Arrange
        mock_settings.TESTING_MODE = False
        mock_settings.PADDLE_ENVIRONMENT = "production"
        mock_settings.PADDLE_VENDOR_ID = "12345"
        mock_settings.PADDLE_VENDOR_AUTH_CODE = "auth_code"

        checkout_request = PaddleCheckoutRequest(
            product_id=123,
            customer_email="test@example.com"
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": False,
            "error": {"message": "Invalid product ID"}
        }
        mock_requests_post.return_value = mock_response

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            self.payment_service.generate_checkout_url(checkout_request)

        assert "Paddle API error: Invalid product ID" in str(exc_info.value)

    @patch("app.services.payment.settings")
    @patch("app.services.payment.requests.post")
    def test_generate_checkout_url_request_error(self, mock_requests_post, mock_settings):
        """Test checkout URL generation with request error"""
        # Arrange
        mock_settings.TESTING_MODE = False
        mock_settings.PADDLE_ENVIRONMENT = "production"

        checkout_request = PaddleCheckoutRequest(
            product_id=123,
            customer_email="test@example.com"
        )

        mock_requests_post.side_effect = Exception("Network error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            self.payment_service.generate_checkout_url(checkout_request)

        assert "Network error" in str(exc_info.value)

    @patch("app.services.payment.settings")
    def test_verify_webhook_signature_testing_mode(self, mock_settings):
        """Test webhook signature verification in testing mode"""
        # Arrange
        mock_settings.TESTING_MODE = True
        request_body = b"test body"
        signature = "test signature"

        # Act
        result = self.payment_service.verify_webhook_signature(request_body, signature)

        # Assert
        assert result is True

    @patch("app.services.payment.settings")
    def test_verify_webhook_signature_no_signature(self, mock_settings):
        """Test webhook signature verification with no signature"""
        # Arrange
        mock_settings.TESTING_MODE = False
        request_body = b"test body"
        signature = ""

        # Act
        result = self.payment_service.verify_webhook_signature(request_body, signature)

        # Assert
        assert result is False

    @patch("app.services.payment.settings")
    @patch("app.services.payment.hmac.compare_digest")
    @patch("app.services.payment.hmac.new")
    def test_verify_webhook_signature_success(self, mock_hmac_new, mock_compare_digest, mock_settings):
        """Test successful webhook signature verification"""
        # Arrange
        mock_settings.TESTING_MODE = False
        mock_settings.PADDLE_PUBLIC_KEY = "public_key"

        request_body = b"test body"
        signature = "expected_signature"

        mock_hmac_instance = MagicMock()
        mock_hmac_instance.hexdigest.return_value = "computed_signature"
        mock_hmac_new.return_value = mock_hmac_instance
        mock_compare_digest.return_value = True

        # Act
        result = self.payment_service.verify_webhook_signature(request_body, signature)

        # Assert
        assert result is True

        # Verify HMAC operations
        mock_hmac_new.assert_called_once_with(
            key=b"public_key",
            msg=request_body,
            digestmod=pytest.importorskip("hashlib").sha1
        )
        mock_hmac_instance.hexdigest.assert_called_once()
        mock_compare_digest.assert_called_once_with("computed_signature", signature)

    @patch("app.services.payment.settings")
    @patch("app.services.payment.hmac.compare_digest")
    @patch("app.services.payment.hmac.new")
    def test_verify_webhook_signature_failure(self, mock_hmac_new, mock_compare_digest, mock_settings):
        """Test failed webhook signature verification"""
        # Arrange
        mock_settings.TESTING_MODE = False
        mock_settings.PADDLE_PUBLIC_KEY = "public_key"

        request_body = b"test body"
        signature = "wrong_signature"

        mock_hmac_instance = MagicMock()
        mock_hmac_instance.hexdigest.return_value = "computed_signature"
        mock_hmac_new.return_value = mock_hmac_instance
        mock_compare_digest.return_value = False

        # Act
        result = self.payment_service.verify_webhook_signature(request_body, signature)

        # Assert
        assert result is False

        mock_compare_digest.assert_called_once_with("computed_signature", signature)