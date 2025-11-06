import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from io import BytesIO

from app.services.storage import StorageService
from fastapi import UploadFile
from starlette.datastructures import Headers


class TestStorageService:
    def setup_method(self):
        self.storage_service = StorageService()
        self.storage_service.s3_client = MagicMock()
        self.storage_service.bucket_name = "test-bucket"

    @patch("app.services.storage.boto3.client")
    @patch("app.services.storage.settings")
    def test_init(self, mock_settings, mock_boto3_client):
        """Test StorageService initialization"""
        # Arrange
        mock_settings.AWS_ACCESS_KEY_ID = "test_key"
        mock_settings.AWS_SECRET_ACCESS_KEY = "test_secret"
        mock_settings.AWS_REGION = "us-east-1"
        mock_settings.S3_BUCKET_NAME = "test-bucket"

        # Act
        service = StorageService()

        # Assert
        mock_boto3_client.assert_called_once_with(
            's3',
            aws_access_key_id="test_key",
            aws_secret_access_key="test_secret",
            region_name="us-east-1"
        )
        assert service.bucket_name == "test-bucket"

    @patch("app.services.storage.settings")
    @pytest.mark.asyncio
    async def test_upload_file_success(self, mock_settings):
        """Test successful file upload"""
        # Arrange
        mock_settings.AWS_REGION = "us-east-1"
        mock_settings.S3_BUCKET_NAME = "test-bucket"

        file_content = b"test file content"
        headers = Headers({"content-type": "application/pdf"})
        file = UploadFile(filename="test.pdf", file=BytesIO(file_content), headers=headers)
        key = "uploads/test.pdf"

        # Act
        result = await self.storage_service.upload_file(file, key)

        # Assert
        self.storage_service.s3_client.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key=key,
            Body=file_content,
            ContentType="application/pdf"
        )
        expected_url = "https://test-bucket.s3.us-east-1.amazonaws.com/uploads/test.pdf"
        assert result == expected_url

    @pytest.mark.asyncio
    async def test_upload_file_no_credentials(self):
        """Test upload file with no AWS credentials"""
        # Arrange
        from botocore.exceptions import NoCredentialsError
        self.storage_service.s3_client.put_object.side_effect = NoCredentialsError()

        file = UploadFile(filename="test.pdf", file=BytesIO(b"content"))
        key = "uploads/test.pdf"

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await self.storage_service.upload_file(file, key)

        assert "AWS credentials not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upload_file_client_error(self):
        """Test upload file with S3 client error"""
        # Arrange
        from botocore.exceptions import ClientError
        error = ClientError({"Error": {"Code": "InternalError", "Message": "Internal error"}}, "PutObject")
        self.storage_service.s3_client.put_object.side_effect = error

        file = UploadFile(filename="test.pdf", file=BytesIO(b"content"))
        key = "uploads/test.pdf"

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await self.storage_service.upload_file(file, key)

        assert "S3 upload failed" in str(exc_info.value)

    @patch("app.services.storage.settings")
    def test_upload_file_data_success(self, mock_settings):
        """Test successful file data upload"""
        # Arrange
        mock_settings.AWS_REGION = "us-east-1"
        mock_settings.S3_BUCKET_NAME = "test-bucket"

        file_data = b"test file data"
        key = "uploads/test.pdf"
        content_type = "application/pdf"

        # Act
        result = self.storage_service.upload_file_data(file_data, key, content_type)

        # Assert
        self.storage_service.s3_client.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key=key,
            Body=file_data,
            ContentType=content_type
        )
        expected_url = "https://test-bucket.s3.us-east-1.amazonaws.com/uploads/test.pdf"
        assert result == expected_url

    def test_upload_file_data_no_credentials(self):
        """Test upload file data with no AWS credentials"""
        # Arrange
        from botocore.exceptions import NoCredentialsError
        self.storage_service.s3_client.put_object.side_effect = NoCredentialsError()

        file_data = b"test data"
        key = "uploads/test.pdf"

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            self.storage_service.upload_file_data(file_data, key)

        assert "AWS credentials not found" in str(exc_info.value)

    def test_download_file_success(self):
        """Test successful file download"""
        # Arrange
        key = "uploads/test.pdf"
        file_content = b"downloaded content"
        mock_body = MagicMock()
        mock_body.read.return_value = file_content
        self.storage_service.s3_client.get_object.return_value = {"Body": mock_body}

        # Act
        result = self.storage_service.download_file(key)

        # Assert
        self.storage_service.s3_client.get_object.assert_called_once_with(Bucket=self.storage_service.bucket_name, Key=key)
        assert result == file_content

    def test_download_file_not_found(self):
        """Test download file that doesn't exist"""
        # Arrange
        from botocore.exceptions import ClientError
        key = "uploads/missing.pdf"
        error = ClientError({"Error": {"Code": "NoSuchKey", "Message": "The specified key does not exist."}}, "GetObject")
        self.storage_service.s3_client.get_object.side_effect = error

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            self.storage_service.download_file(key)

        assert "File not found" in str(exc_info.value)

    def test_download_file_client_error(self):
        """Test download file with other S3 client error"""
        # Arrange
        from botocore.exceptions import ClientError
        key = "uploads/test.pdf"
        error = ClientError({"Error": {"Code": "InternalError", "Message": "Internal error"}}, "GetObject")
        self.storage_service.s3_client.get_object.side_effect = error

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            self.storage_service.download_file(key)

        assert "S3 download failed" in str(exc_info.value)

    def test_delete_file_success(self):
        """Test successful file deletion"""
        # Arrange
        key = "uploads/test.pdf"

        # Act
        result = self.storage_service.delete_file(key)

        # Assert
        self.storage_service.s3_client.delete_object.assert_called_once_with(Bucket=self.storage_service.bucket_name, Key=key)
        assert result is True

    def test_delete_file_client_error(self):
        """Test delete file with S3 client error"""
        # Arrange
        from botocore.exceptions import ClientError
        key = "uploads/test.pdf"
        error = ClientError({"Error": {"Code": "InternalError", "Message": "Internal error"}}, "DeleteObject")
        self.storage_service.s3_client.delete_object.side_effect = error

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            self.storage_service.delete_file(key)

        assert "S3 delete failed" in str(exc_info.value)

    def test_generate_presigned_url_success(self):
        """Test successful presigned URL generation"""
        # Arrange
        key = "uploads/test.pdf"
        expiration = 7200
        expected_url = "https://presigned-url.example.com"
        self.storage_service.s3_client.generate_presigned_url.return_value = expected_url

        # Act
        result = self.storage_service.generate_presigned_url(key, expiration)

        # Assert
        self.storage_service.s3_client.generate_presigned_url.assert_called_once_with(
            'get_object',
            Params={'Bucket': self.storage_service.bucket_name, 'Key': key},
            ExpiresIn=expiration
        )
        assert result == expected_url

    def test_generate_presigned_url_default_expiration(self):
        """Test presigned URL generation with default expiration"""
        # Arrange
        key = "uploads/test.pdf"
        expected_url = "https://presigned-url.example.com"
        self.storage_service.s3_client.generate_presigned_url.return_value = expected_url

        # Act
        result = self.storage_service.generate_presigned_url(key)

        # Assert
        self.storage_service.s3_client.generate_presigned_url.assert_called_once_with(
            'get_object',
            Params={'Bucket': self.storage_service.bucket_name, 'Key': key},
            ExpiresIn=3600  # default expiration
        )
        assert result == expected_url

    def test_generate_presigned_url_client_error(self):
        """Test presigned URL generation with S3 client error"""
        # Arrange
        from botocore.exceptions import ClientError
        key = "uploads/test.pdf"
        error = ClientError({"Error": {"Code": "InternalError", "Message": "Internal error"}}, "GeneratePresignedUrl")
        self.storage_service.s3_client.generate_presigned_url.side_effect = error

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            self.storage_service.generate_presigned_url(key)

        assert "Failed to generate presigned URL" in str(exc_info.value)