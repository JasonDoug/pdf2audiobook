# Google Cloud & Azure Integration Guide

This guide explains how to use Google Cloud and Azure services for storage and text-to-speech in the PDF2Audiobook application.

## 🎤 Text-to-Speech Providers

### Google Cloud Text-to-Speech

**Already implemented** in `worker/pdf_pipeline.py` as `GoogleTTS` class.

#### Setup:
1. **Enable the API**: Go to [Google Cloud Console](https://console.cloud.google.com) → APIs & Services → Enable "Cloud Text-to-Speech API"

2. **Create Service Account**:
   ```bash
   gcloud iam service-accounts create pdf2audiobook-tts
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:pdf2audiobook-tts@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/cloudtranslate.user"
   ```

3. **Download Credentials**: Create and download a JSON key file

4. **Environment Variables**:
   ```env
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
   GOOGLE_CLOUD_PROJECT=your-project-id
   ```

#### Available Voices:
- `en-US-Neural2-D` (default)
- `en-US-Neural2-F`
- `en-GB-Neural2-B`
- `en-AU-Neural2-D`
- Many more available in the [documentation](https://cloud.google.com/text-to-speech/docs/voices)

### Azure Cognitive Services Speech

**Already implemented** in `worker/pdf_pipeline.py` as `AzureTTS` class.

#### Setup:
1. **Create Resource**: Go to [Azure Portal](https://portal.azure.com) → Create "Speech" resource

2. **Get Keys**: Copy the "Key 1" and "Location/Region" from the resource

3. **Environment Variables**:
   ```env
   AZURE_SPEECH_KEY=your-speech-key
   AZURE_SPEECH_REGION=eastus
   ```

#### Available Voices:
- `en-US-JennyNeural` (default)
- `en-US-AriaNeural`
- `en-GB-SoniaNeural`
- `en-AU-NatashaNeural`
- Full list in [Azure documentation](https://speech.microsoft.com/portal/voicegallery)

## ☁️ Cloud Storage Providers

### Google Cloud Storage

**Implementation**: `backend/app/services/cloud_storage.py` - `GoogleCloudStorageService`

#### Setup:
1. **Enable APIs**: Cloud Storage API and Cloud Storage JSON API

2. **Create Bucket**:
   ```bash
   gsutil mb -p YOUR_PROJECT_ID gs://your-bucket-name
   ```

3. **Service Account**: Use the same service account as TTS or create a new one with "Storage Object Admin" role

4. **Environment Variables**:
   ```env
   STORAGE_PROVIDER=gcp
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
   GCS_BUCKET_NAME=your-bucket-name
   ```

### Azure Blob Storage

**Implementation**: `backend/app/services/cloud_storage.py` - `AzureBlobStorageService`

#### Setup:
1. **Create Storage Account**: Azure Portal → Storage Accounts → Create

2. **Get Access Keys**: Storage Account → Access Keys → Copy "Key 1"

3. **Create Container** (optional - auto-created by code):
   ```bash
   az storage container create --name pdf2audiobook --account-name yourstorageaccount
   ```

4. **Environment Variables**:
   ```env
   STORAGE_PROVIDER=azure
   AZURE_STORAGE_ACCOUNT=your-storage-account-name
   AZURE_STORAGE_KEY=your-storage-account-key
   AZURE_CONTAINER_NAME=pdf2audiobook
   ```

## 🔧 Configuration

### Switching Providers

Update your environment variables to switch providers:

```env
# For Google Cloud
STORAGE_PROVIDER=gcp
# TTS automatically uses Google when credentials are available

# For Azure
STORAGE_PROVIDER=azure
# TTS automatically uses Azure when AZURE_SPEECH_KEY is set
```

### Provider Priority

The application automatically detects available providers:

1. **TTS**: Checks for credentials in order: OpenAI → Google Cloud → Azure → AWS Polly → ElevenLabs
2. **Storage**: Uses the `STORAGE_PROVIDER` environment variable

## 📋 Required Dependencies

Add these to your `pyproject.toml` or `requirements.txt`:

```toml
# Google Cloud
google-cloud-texttospeech = "^2.14.1"
google-cloud-storage = "^2.10.0"

# Azure
azure-cognitiveservices-speech = "^1.32.1"
azure-storage-blob = "^12.17.0"
azure-identity = "^1.13.0"
```

## 🚀 Usage Examples

### Using Google Cloud TTS

```python
from worker.pdf_pipeline import TTSManager

# Automatically uses Google Cloud if credentials are available
tts_manager = TTSManager()
audio_data = tts_manager.text_to_audio(
    text="Hello world",
    provider="google",
    voice_id="en-US-Neural2-D",
    speed=1.0
)
```

### Using Azure Storage

```python
from app.services.cloud_storage import create_storage_service

# Automatically creates Azure Blob Storage service
storage = create_storage_service("azure")
url = await storage.upload_file(file, "path/to/file.pdf")
```

## 💰 Pricing Comparison

### Text-to-Speech (per 1M characters)

| Provider | Standard | Neural/WaveNet |
|----------|----------|----------------|
| Google Cloud | $4.00 | $16.00 |
| Azure | $15.00 | $15.00 (Neural) |
| AWS Polly | $4.00 | $16.00 |
| OpenAI | $15.00 | N/A |

### Cloud Storage (per GB/month)

| Provider | Standard | Infrequent Access |
|----------|----------|-------------------|
| AWS S3 | $0.023 | $0.0125 |
| Google Cloud Storage | $0.020 | $0.010 |
| Azure Blob | $0.018 | $0.015 |

## 🔒 Security Best Practices

### Google Cloud
- Use service account keys with minimal required permissions
- Rotate keys regularly
- Store credentials securely (not in code)

### Azure
- Use Azure Key Vault for secret management
- Implement Azure AD authentication when possible
- Use managed identities for Azure resources

## 🐛 Troubleshooting

### Google Cloud Issues
- **"403 Forbidden"**: Check service account permissions
- **"Project not found"**: Verify `GOOGLE_CLOUD_PROJECT` is set
- **"API not enabled"**: Enable required APIs in Google Cloud Console

### Azure Issues
- **"Invalid credentials"**: Check `AZURE_SPEECH_KEY` and region
- **"Resource not found"**: Verify storage account and container names
- **"Access denied"**: Check storage account access keys

## 📚 Additional Resources

- [Google Cloud Text-to-Speech Docs](https://cloud.google.com/text-to-speech/docs)
- [Azure Cognitive Services Speech](https://docs.microsoft.com/en-us/azure/cognitive-services/speech-service/)
- [Google Cloud Storage Docs](https://cloud.google.com/storage/docs)
- [Azure Blob Storage Docs](https://docs.microsoft.com/en-us/azure/storage/blobs/)