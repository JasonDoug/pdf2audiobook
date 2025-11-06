# Manual API Testing Guide

This guide provides instructions on how to start the development server and manually test the PDF-to-audio workflow using `curl` commands, bypassing the automated Celery worker.

## 1. Starting the Development Server

This project is fully containerized using Docker.

### Prerequisites
- Docker
- Docker Compose

### Steps

1.  **Set up Environment Variables**:
    Copy the example environment file and fill in the required values. At a minimum, you need valid AWS credentials to test the file upload flow.

    ```bash
    cp .env.example .env
    ```

    Edit the `.env` file with your credentials.

2.  **Build and Run the Services**:
    This command will build the Docker images for the backend, frontend, and worker, and start all the necessary services (including the database and Redis).

    ```bash
    docker-compose up --build
    ```

3.  **Verify Services are Running**:
    -   **Backend API**: Should be running at `http://localhost:8000`.
    -   **API Docs**: You can view the interactive API documentation at `http://localhost:8000/docs`.
    -   **Frontend**: Should be running at `http://localhost:3000`.

---

## 2. Manual PDF Processing Flow via API

This series of `curl` commands simulates the entire lifecycle of a job, which is normally handled by the Celery worker.

### Prerequisites

-   A valid JWT for an authenticated user. Since this project uses Clerk for authentication, you would typically get this token from your frontend after a user logs in. For this guide, we will use a placeholder `DUMMY_JWT`.
-   The `jq` command-line tool is used to extract the `job_id` from the response. You can install it or manually copy the ID.

### Step 1: Create a New Job

This command uploads a PDF (`dummy.pdf`) and creates a new job record. The job will have a `pending` status.

```bash
# Replace DUMMY_JWT with your actual JWT
export JWT="DUMMY_JWT"

# Submit the PDF to create the job
curl -X POST "http://localhost:8000/api/v1/jobs/" \
  -H "Authorization: Bearer $JWT" \
  -F "file=@dummy.pdf" \
  -F "voice_provider=openai" \
  -F "voice_type=nova"
```

**Expected Response:**

You will get a JSON response representing the newly created job. Note the `id` and `status: "pending"`.

```json
{
  "original_filename": "dummy.pdf",
  "voice_provider": "openai",
  "voice_type": "nova",
  "reading_speed": 1.0,
  "include_summary": false,
  "id": 1,
  "user_id": 1,
  "pdf_s3_key": "pdfs/1/dummy.pdf",
  "audio_s3_key": null,
  "pdf_s3_url": "https://your-bucket.s3.amazonaws.com/pdfs/1/dummy.pdf",
  "audio_s3_url": null,
  "status": "pending",
  "progress_percentage": 0,
  "error_message": null,
  "created_at": "2023-11-16T12:00:00.000000Z",
  "started_at": null,
  "completed_at": null
}
```

### Step 2: Manually Set the Job to "Processing"

Now, we simulate the worker picking up the job. We use the `PATCH` endpoint we added to update the job's status.

```bash
# Extract the job ID from the previous response (or set it manually)
export JOB_ID=1 

# Update the job status to processing
curl -X PATCH "http://localhost:8000/api/v1/jobs/$JOB_ID" \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "processing",
    "progress_percentage": 25
  }'
```

### Step 3: Manually Set the Job to "Completed"

Here, we simulate the worker having successfully finished the conversion. We update the status to `completed` and provide a (dummy) URL for the finished audio file.

```bash
# Update the job status to completed
curl -X PATCH "http://localhost:8000/api/v1/jobs/$JOB_ID" \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed",
    "progress_percentage": 100,
    "audio_s3_url": "https://your-bucket.s3.amazonaws.com/audio/1/dummy.mp3"
  }'
```

### Step 4: Verify the Final Job Status

Finally, let's retrieve the job details to confirm that it has been fully updated.

```bash
# Get the final job details
curl -X GET "http://localhost:8000/api/v1/jobs/$JOB_ID" \
  -H "Authorization: Bearer $JWT"
```

**Expected Response:**

The job status is now `completed`, and the `audio_s3_url` is populated.

```json
{
  "original_filename": "dummy.pdf",
  "voice_provider": "openai",
  "voice_type": "nova",
  // ...
  "id": 1,
  "audio_s3_url": "https://your-bucket.s3.amazonaws.com/audio/1/dummy.mp3",
  "status": "completed",
  "progress_percentage": 100,
  // ...
  "completed_at": "2023-11-16T12:05:00.000000Z"
}
```

This completes the manual, worker-less testing flow for a PDF conversion job.