import os
import asyncio
from typing import Optional
from fastapi import UploadFile
from google.cloud import storage as gcs
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError

from app.core.config import settings


class GoogleCloudStorageService:
    """Google Cloud Storage implementation"""

    def __init__(self):
        # Set credentials from environment variable or service account
        if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            self.client = gcs.Client()
        else:
            # Use service account key from environment
            import json
            from google.oauth2 import service_account

            credentials_dict = json.loads(os.getenv("GOOGLE_CREDENTIALS_JSON", "{}"))
            credentials = service_account.Credentials.from_service_account_info(credentials_dict)
            self.client = gcs.Client(credentials=credentials)

        self.bucket_name = os.getenv("GCS_BUCKET_NAME", settings.S3_BUCKET_NAME)

    async def upload_file(self, file: UploadFile, key: str) -> str:
        """Upload a file to Google Cloud Storage"""
        try:
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(key)

            # Read file content
            file_content = await file.read()

            # Upload in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: blob.upload_from_string(file_content))

            # Make public if needed
            blob.make_public()

            return blob.public_url

        except Exception as e:
            raise Exception(f"GCS upload failed: {str(e)}")

    async def download_file(self, key: str) -> bytes:
        """Download a file from Google Cloud Storage"""
        try:
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(key)

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: blob.download_as_bytes())

        except Exception as e:
            raise Exception(f"GCS download failed: {str(e)}")

    async def delete_file(self, key: str) -> bool:
        """Delete a file from Google Cloud Storage"""
        try:
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(key)

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: blob.delete())

            return True

        except Exception as e:
            raise Exception(f"GCS delete failed: {str(e)}")

    async def generate_presigned_url(self, key: str, expiration: int = 3600) -> str:
        """Generate a signed URL for temporary access"""
        try:
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(key)

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                lambda: blob.generate_signed_url(expiration=expiration)
            )

        except Exception as e:
            raise Exception(f"GCS signed URL generation failed: {str(e)}")


class AzureBlobStorageService:
    """Azure Blob Storage implementation"""

    def __init__(self):
        account_url = f"https://{os.getenv('AZURE_STORAGE_ACCOUNT')}.blob.core.windows.net"
        self.blob_service_client = BlobServiceClient(
            account_url=account_url,
            credential=os.getenv("AZURE_STORAGE_KEY")
        )
        self.container_name = os.getenv("AZURE_CONTAINER_NAME", "pdf2audiobook")

        # Create container if it doesn't exist
        try:
            self.blob_service_client.create_container(self.container_name)
        except ResourceExistsError:
            pass  # Container already exists

    async def upload_file(self, file: UploadFile, key: str) -> str:
        """Upload a file to Azure Blob Storage"""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=key
            )

            # Read file content
            file_content = await file.read()

            # Upload in thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: blob_client.upload_blob(file_content, overwrite=True)
            )

            return blob_client.url

        except Exception as e:
            raise Exception(f"Azure Blob upload failed: {str(e)}")

    async def download_file(self, key: str) -> bytes:
        """Download a file from Azure Blob Storage"""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=key
            )

            loop = asyncio.get_event_loop()
            download_stream = await loop.run_in_executor(None, lambda: blob_client.download_blob())
            return await loop.run_in_executor(None, lambda: download_stream.readall())

        except Exception as e:
            raise Exception(f"Azure Blob download failed: {str(e)}")

    async def delete_file(self, key: str) -> bool:
        """Delete a file from Azure Blob Storage"""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=key
            )

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: blob_client.delete_blob())

            return True

        except Exception as e:
            raise Exception(f"Azure Blob delete failed: {str(e)}")

    async def generate_presigned_url(self, key: str, expiration: int = 3600) -> str:
        """Generate a SAS URL for temporary access"""
        try:
            from datetime import datetime, timedelta
            from azure.storage.blob import BlobSasPermissions, generate_blob_sas

            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=key
            )

            # Generate SAS token
            sas_token = generate_blob_sas(
                account_name=self.blob_service_client.account_name,
                container_name=self.container_name,
                blob_name=key,
                account_key=os.getenv("AZURE_STORAGE_KEY"),
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(seconds=expiration)
            )

            return f"{blob_client.url}?{sas_token}"

        except Exception as e:
            raise Exception(f"Azure SAS URL generation failed: {str(e)}")


# Factory function to create the appropriate storage service
def create_storage_service(provider: str = "aws") -> 'StorageService':
    """Factory function to create storage service based on provider"""
    if provider.lower() == "gcp" or provider.lower() == "google":
        return GoogleCloudStorageService()
    elif provider.lower() == "azure":
        return AzureBlobStorageService()
    else:
        # Default to AWS S3
        from app.services.storage import StorageService
        return StorageService()