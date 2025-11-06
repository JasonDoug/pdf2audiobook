import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from app.services.job import JobService
from app.models import Job, User, JobStatus, SubscriptionTier, ConversionMode
from app.schemas import JobCreate, VoiceProvider


class TestJobService:
    def setup_method(self):
        self.db = MagicMock()
        self.job_service = JobService(self.db)

    def test_create_job(self):
        """Test creating a new job"""
        # Arrange
        user_id = 1
        job_data = JobCreate(
            original_filename="test.pdf",
            voice_provider=VoiceProvider.OPENAI,
            voice_type="default",
            reading_speed=1.0,
            include_summary=False,
            conversion_mode=ConversionMode.FULL
        )
        pdf_s3_key = "pdfs/test.pdf"
        pdf_s3_url = "https://s3.amazonaws.com/bucket/pdfs/test.pdf"

        # Act
        job = self.job_service.create_job(user_id, job_data, pdf_s3_key, pdf_s3_url)

        # Assert
        assert job.user_id == user_id
        assert job.original_filename == job_data.original_filename
        assert job.pdf_s3_key == pdf_s3_key
        assert job.pdf_s3_url == pdf_s3_url
        assert job.voice_provider == job_data.voice_provider
        assert job.voice_type == job_data.voice_type
        assert job.reading_speed == job_data.reading_speed
        assert job.include_summary == job_data.include_summary
        assert job.conversion_mode == job_data.conversion_mode
        assert job.status == JobStatus.PENDING

        self.db.add.assert_called_once_with(job)
        self.db.commit.assert_called_once()

    def test_get_user_job_found(self):
        """Test getting a user's job when it exists"""
        # Arrange
        user_id = 1
        job_id = 123
        mock_job = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = mock_job

        # Act
        result = self.job_service.get_user_job(user_id, job_id)

        # Assert
        assert result == mock_job
        self.db.query.assert_called_once_with(Job)
        self.db.query.return_value.filter.assert_called_once()

    def test_get_user_job_not_found(self):
        """Test getting a user's job when it doesn't exist"""
        # Arrange
        user_id = 1
        job_id = 123
        self.db.query.return_value.filter.return_value.first.return_value = None

        # Act
        result = self.job_service.get_user_job(user_id, job_id)

        # Assert
        assert result is None

    def test_get_user_jobs(self):
        """Test getting all jobs for a user"""
        # Arrange
        user_id = 1
        skip = 10
        limit = 20
        mock_jobs = [MagicMock(), MagicMock()]
        query_chain = self.db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit
        query_chain.return_value.all.return_value = mock_jobs

        # Act
        result = self.job_service.get_user_jobs(user_id, skip, limit)

        # Assert
        assert result == mock_jobs
        self.db.query.assert_called_once_with(Job)
        self.db.query.return_value.filter.assert_called_once()
        self.db.query.return_value.filter.return_value.order_by.assert_called_once()
        self.db.query.return_value.filter.return_value.order_by.return_value.offset.assert_called_once_with(skip)
        self.db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.assert_called_once_with(limit)

    def test_update_job_success(self):
        """Test updating a job successfully"""
        # Arrange
        job_id = 123
        job_update = {"status": JobStatus.COMPLETED, "progress_percentage": 100}
        mock_job = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = mock_job

        # Act
        result = self.job_service.update_job(job_id, job_update)

        # Assert
        assert result == mock_job
        assert mock_job.status == JobStatus.COMPLETED
        assert mock_job.progress_percentage == 100
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once_with(mock_job)

    def test_update_job_not_found(self):
        """Test updating a job that doesn't exist"""
        # Arrange
        job_id = 123
        job_update = {"status": JobStatus.COMPLETED}
        self.db.query.return_value.filter.return_value.first.return_value = None

        # Act
        result = self.job_service.update_job(job_id, job_update)

        # Assert
        assert result is None
        self.db.commit.assert_not_called()
        self.db.refresh.assert_not_called()

    @patch("app.services.job.datetime")
    def test_update_job_status_processing(self, mock_datetime):
        """Test updating job status to PROCESSING"""
        # Arrange
        job_id = 123
        status = JobStatus.PROCESSING
        progress = 50
        mock_job = MagicMock()
        mock_job.started_at = None
        mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0)
        self.db.query.return_value.filter.return_value.first.return_value = mock_job

        # Act
        result = self.job_service.update_job_status(job_id, status, progress)

        # Assert
        assert result == mock_job
        assert mock_job.status == status
        assert mock_job.progress_percentage == progress
        assert mock_job.started_at == datetime(2024, 1, 1, 12, 0, 0)
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once_with(mock_job)

    @patch("app.services.job.datetime")
    def test_update_job_status_completed(self, mock_datetime):
        """Test updating job status to COMPLETED"""
        # Arrange
        job_id = 123
        status = JobStatus.COMPLETED
        progress = None
        mock_job = MagicMock()
        mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0)
        self.db.query.return_value.filter.return_value.first.return_value = mock_job

        # Act
        result = self.job_service.update_job_status(job_id, status, progress)

        # Assert
        assert result == mock_job
        assert mock_job.status == status
        assert mock_job.completed_at == datetime(2024, 1, 1, 12, 0, 0)
        assert mock_job.progress_percentage == 100
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once_with(mock_job)

    def test_update_job_status_with_error_message(self):
        """Test updating job status with error message"""
        # Arrange
        job_id = 123
        status = JobStatus.FAILED
        error_message = "Processing failed"
        mock_job = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = mock_job

        # Act
        result = self.job_service.update_job_status(job_id, status, error_message=error_message)

        # Assert
        assert result == mock_job
        assert mock_job.status == status
        assert mock_job.error_message == error_message
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once_with(mock_job)

    @patch("app.core.config.settings")
    def test_can_user_create_job_testing_mode(self, mock_settings):
        """Test can_user_create_job in testing mode"""
        # Arrange
        mock_settings.TESTING_MODE = True
        user_id = 1

        # Act
        result = self.job_service.can_user_create_job(user_id)

        # Assert
        assert result is True
        self.db.query.assert_not_called()

    @patch("app.core.config.settings")
    def test_can_user_create_job_free_tier_under_limit(self, mock_settings):
        """Test can_user_create_job for free tier user under monthly limit"""
        # Arrange
        mock_settings.TESTING_MODE = False
        user_id = 1
        mock_user = MagicMock()
        mock_user.subscription_tier.value = "free"
        mock_user.one_time_credits = 0
        self.db.query.return_value.filter.return_value.first.return_value = mock_user
        # Mock count query for monthly jobs
        self.db.query.return_value.filter.return_value.count.return_value = 1

        # Act
        result = self.job_service.can_user_create_job(user_id)

        # Assert
        assert result is True

    @patch("app.core.config.settings")
    def test_can_user_create_job_free_tier_at_limit(self, mock_settings):
        """Test can_user_create_job for free tier user at monthly limit"""
        # Arrange
        mock_settings.TESTING_MODE = False
        user_id = 1
        mock_user = MagicMock()
        mock_user.subscription_tier.value = "free"
        mock_user.one_time_credits = 0
        self.db.query.return_value.filter.return_value.first.return_value = mock_user
        # Mock count query for monthly jobs - at limit
        self.db.query.return_value.filter.return_value.count.return_value = 2

        # Act
        result = self.job_service.can_user_create_job(user_id)

        # Assert
        assert result is False

    @patch("app.core.config.settings")
    def test_can_user_create_job_pro_tier_under_limit(self, mock_settings):
        """Test can_user_create_job for pro tier user under monthly limit"""
        # Arrange
        mock_settings.TESTING_MODE = False
        user_id = 1
        mock_user = MagicMock()
        mock_user.subscription_tier.value = "pro"
        mock_user.one_time_credits = 0
        self.db.query.return_value.filter.return_value.first.return_value = mock_user
        # Mock count query for monthly jobs
        self.db.query.return_value.filter.return_value.count.return_value = 25

        # Act
        result = self.job_service.can_user_create_job(user_id)

        # Assert
        assert result is True

    @patch("app.core.config.settings")
    def test_can_user_create_job_enterprise_unlimited(self, mock_settings):
        """Test can_user_create_job for enterprise tier user (unlimited)"""
        # Arrange
        mock_settings.TESTING_MODE = False
        user_id = 1
        mock_user = MagicMock()
        mock_user.subscription_tier.value = "enterprise"
        mock_user.one_time_credits = 0
        self.db.query.return_value.filter.return_value.first.return_value = mock_user

        # Act
        result = self.job_service.can_user_create_job(user_id)

        # Assert
        assert result is True

    @patch("app.core.config.settings")
    def test_can_user_create_job_with_one_time_credits(self, mock_settings):
        """Test can_user_create_job when user has one-time credits"""
        # Arrange
        mock_settings.TESTING_MODE = False
        user_id = 1
        mock_user = MagicMock()
        mock_user.subscription_tier.value = "free"
        mock_user.one_time_credits = 5
        self.db.query.return_value.filter.return_value.first.return_value = mock_user

        # Mock the count query to return jobs over the free tier limit
        count_mock = MagicMock()
        count_mock.return_value = 3  # Over free tier limit of 2
        self.db.query.return_value.filter.return_value.count = count_mock

        # Act
        result = self.job_service.can_user_create_job(user_id)

        # Assert
        assert result is True

    @patch("app.core.config.settings")
    def test_can_user_create_job_user_not_found(self, mock_settings):
        """Test can_user_create_job when user doesn't exist"""
        # Arrange
        mock_settings.TESTING_MODE = False
        user_id = 1
        self.db.query.return_value.filter.return_value.first.return_value = None

        # Act
        result = self.job_service.can_user_create_job(user_id)

        # Assert
        assert result is False

    def test_consume_credit_success(self):
        """Test consuming a credit successfully"""
        # Arrange
        user_id = 1
        mock_user = MagicMock()
        mock_user.one_time_credits = 5
        self.db.query.return_value.filter.return_value.first.return_value = mock_user

        # Act
        result = self.job_service.consume_credit(user_id)

        # Assert
        assert result is True
        assert mock_user.one_time_credits == 4
        self.db.commit.assert_called_once()

    def test_consume_credit_no_credits(self):
        """Test consuming a credit when user has no credits"""
        # Arrange
        user_id = 1
        mock_user = MagicMock()
        mock_user.one_time_credits = 0
        self.db.query.return_value.filter.return_value.first.return_value = mock_user

        # Act
        result = self.job_service.consume_credit(user_id)

        # Assert
        assert result is False
        assert mock_user.one_time_credits == 0
        self.db.commit.assert_not_called()

    def test_consume_credit_user_not_found(self):
        """Test consuming a credit when user doesn't exist"""
        # Arrange
        user_id = 1
        self.db.query.return_value.filter.return_value.first.return_value = None

        # Act
        result = self.job_service.consume_credit(user_id)

        # Assert
        assert result is False
        self.db.commit.assert_not_called()