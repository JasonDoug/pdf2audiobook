import boto3
import os
import asyncio
from fastapi import UploadFile
from typing import Optional
from botocore.exceptions import NoCredentialsError, ClientError

from app.core.config import settings

class StorageService:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.S3_BUCKET_NAME
    
    async def upload_file(self, file: UploadFile, key: str) -> str:
        """Upload a file to S3 and return its URL"""
        try:
            # Read file content
            file_content = await file.read()
            
            # Upload to S3 asynchronously in a thread pool to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, # Use the default executor
                lambda: self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=file_content,
                    ContentType=file.content_type
                ))
            
            # Generate URL
            url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
            return url
            
        except NoCredentialsError:
            raise Exception("AWS credentials not found")
        except ClientError as e:
            raise Exception(f"S3 upload failed: {str(e)}")
    
    def upload_file_data(self, file_data: bytes, key: str, content_type: str = "application/octet-stream") -> str:
        """Upload file data to S3 and return its URL"""
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=file_data,
                ContentType=content_type
            )
            
            url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
            return url
            
        except NoCredentialsError:
            raise Exception("AWS credentials not found")
        except ClientError as e:
            raise Exception(f"S3 upload failed: {str(e)}")
    
    def download_file(self, key: str) -> bytes:
        """Download a file from S3"""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            return response['Body'].read()
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise Exception(f"File not found: {key}")
            raise Exception(f"S3 download failed: {str(e)}")
    
    def delete_file(self, key: str) -> bool:
        """Delete a file from S3"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
            
        except ClientError as e:
            raise Exception(f"S3 delete failed: {str(e)}")
    
    def generate_presigned_url(self, key: str, expiration: int = 3600) -> Optional[str]:
        """Generate a presigned URL for temporary access"""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=expiration
            )
            return url
            
        except ClientError as e:
            raise Exception(f"Failed to generate presigned URL: {str(e)}")