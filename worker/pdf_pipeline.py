import os
import tempfile
from typing import Optional, Callable, List
import fitz  # PyMuPDF
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import openai
from pydub import AudioSegment
import io
import re
from abc import ABC, abstractmethod

# TTS Provider Imports
from google.cloud import texttospeech
import boto3
from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesizer, ResultReason
from elevenlabs.client import ElevenLabs


# --- TTS PROVIDER INTERFACE ---
class TTSProvider(ABC):
    @abstractmethod
    def text_to_audio(self, text: str, voice_id: str, speed: float) -> bytes:
        pass


# --- CONCRETE TTS IMPLEMENTATIONS ---
class OpenAITTS(TTSProvider):
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.voice_mapping = {"default": "alloy", "female": "nova", "male": "onyx"}

    def text_to_audio(self, text: str, voice_id: str, speed: float) -> bytes:
        voice = self.voice_mapping.get(voice_id, "alloy")
        response = self.client.audio.speech.create(
            model="tts-1", voice=voice, input=text, speed=speed
        )
        return response.content


class GoogleTTS(TTSProvider):
    def __init__(self):
        self.client = texttospeech.TextToSpeechClient()

    def text_to_audio(self, text: str, voice_id: str, speed: float) -> bytes:
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US", name=voice_id or "en-US-Neural2-D"
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3, speaking_rate=speed
        )
        response = self.client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        return response.audio_content


class AWSPollyTTS(TTSProvider):
    def __init__(self):
        self.client = boto3.client(
            "polly",
            region_name=os.getenv("AWS_REGION", "us-east-1"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )

    def text_to_audio(self, text: str, voice_id: str, speed: float) -> bytes:
        # Polly uses SSML for speed control
        rate = f"{int(speed * 100)}%"
        ssml_text = f'<speak><prosody rate="{rate}">{text}</prosody></speak>'
        response = self.client.synthesize_speech(
            Text=ssml_text,
            OutputFormat="mp3",
            VoiceId=voice_id or "Joanna",
            TextType="ssml",
        )
        return response["AudioStream"].read()


class AzureTTS(TTSProvider):
    def __init__(self):
        self.speech_config = SpeechConfig(
            subscription=os.getenv("AZURE_SPEECH_KEY"),
            region=os.getenv("AZURE_SPEECH_REGION"),
        )

    def text_to_audio(self, text: str, voice_id: str, speed: float) -> bytes:
        self.speech_config.speech_synthesis_voice_name = voice_id or "en-US-JennyNeural"
        synthesizer = SpeechSynthesizer(
            speech_config=self.speech_config, audio_config=None
        )
        # Azure uses SSML for speed control
        rate = f"{speed:.2f}"
        ssml_text = f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US"><voice name="{self.speech_config.speech_synthesis_voice_name}"><prosody rate="{rate}">{text}</prosody></voice></speak>'
        result = synthesizer.speak_ssml_async(ssml_text).get()
        if result.reason == ResultReason.SynthesizingAudioCompleted:
            return result.audio_data
        else:
            raise Exception(f"Azure TTS failed: {result.reason}")


class ElevenLabsTTS(TTSProvider):
    def __init__(self):
        self.client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

    def text_to_audio(self, text: str, voice_id: str, speed: float) -> bytes:
        # ElevenLabs does not directly support a speed parameter in the same way
        # Voice settings are managed in the ElevenLabs studio
        audio = self.client.generate(
            text=text, voice=voice_id or "Rachel", model="eleven_multilingual_v2"
        )
        return audio


# --- TTS MANAGER ---
class TTSManager:
    def __init__(self):
        self.providers = {
            "openai": OpenAITTS(),
            "google": GoogleTTS(),
            "aws_polly": AWSPollyTTS(),
            "azure": AzureTTS(),
            "eleven_labs": ElevenLabsTTS(),
        }

    def get_provider(self, provider_name: str) -> TTSProvider:
        provider = self.providers.get(provider_name)
        if not provider:
            raise ValueError(f"Unsupported TTS provider: {provider_name}")
        return provider


# --- PDF PIPELINE ---
class PDFToAudioPipeline:
    def __init__(self):
        self.tts_manager = TTSManager()

    def process_pdf(
        self,
        pdf_path: str,
        voice_provider: str = "openai",
        voice_type: str = "default",
        reading_speed: float = 1.0,
        include_summary: bool = False,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> bytes:
        try:
            if progress_callback:
                progress_callback(5)
            raw_text = self._extract_text(pdf_path)

            if not raw_text.strip():
                raise ValueError("No text could be extracted from the PDF.")

            if progress_callback:
                progress_callback(15)
            cleaned_text = self._advanced_text_cleanup(raw_text)

            final_text = self._get_final_text(
                cleaned_text, include_summary, progress_callback
            )

            if progress_callback:
                progress_callback(35)
            chapters = self._chapterize_text(final_text)

            tts_provider = self.tts_manager.get_provider(voice_provider)

            chapter_audio_segments = []
            for i, chapter_text in enumerate(chapters):
                progress = 40 + int((i / len(chapters)) * 55)
                if progress_callback:
                    progress_callback(progress)

                audio_data = tts_provider.text_to_audio(
                    chapter_text, voice_type, reading_speed
                )
                chapter_audio_segments.append(
                    AudioSegment.from_file(io.BytesIO(audio_data))
                )

            if progress_callback:
                progress_callback(95)
            full_audio_data = self._assemble_audio_chapters(chapter_audio_segments)

            if progress_callback:
                progress_callback(100)
            return full_audio_data

        except Exception as e:
            raise Exception(f"PDF processing failed: {str(e)}")

    def _get_final_text(self, cleaned_text, include_summary, progress_callback):
        if include_summary:
            if progress_callback:
                progress_callback(25)
            summary = self._generate_summary(cleaned_text)
            return f"Summary of the document: {summary}\n\n{cleaned_text}"
        return cleaned_text

    def _extract_text(self, pdf_path: str) -> str:
        text = ""
        try:
            with fitz.open(pdf_path) as doc:
                for page in doc:
                    text += page.get_text()
            if len(text.strip()) < 100:  # Threshold for considering OCR
                return self._ocr_pdf(pdf_path)
            return text
        except Exception:
            return self._ocr_pdf(pdf_path)

    def _ocr_pdf(self, pdf_path: str) -> str:
        text = ""
        try:
            images = convert_from_path(pdf_path, dpi=300)
            for image in images:
                text += pytesseract.image_to_string(image, lang="eng") + "\n"
            return text
        except Exception as e:
            raise Exception(f"OCR extraction failed: {str(e)}")

    def _advanced_text_cleanup(self, text: str) -> str:
        text = re.sub(r"\n\s*\n", "\n", text)
        text = re.sub(r"\s+", " ", text)
        replacements = {
            "â": "-",
            "â": '"',
            "â": '"',
            "â": "'",
            "â¦": "...",
            "â¢": "*",
            "â€™": "'",
            "â€˜": "'",
            "â€œ": '"',
            "â€ť": '"',
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        text = text.replace("ﬁ", "fi").replace("ﬂ", "fl")
        text = re.sub(r"\s{2,}", " ", text)
        return text.strip()

    def _generate_summary(self, text: str) -> str:
        try:
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            max_length = 12000
            truncated_text = text[:max_length] if len(text) > max_length else text

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "Summarize the following text in about 150 words.",
                    },
                    {"role": "user", "content": truncated_text},
                ],
                max_tokens=250,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return text[:500] + "..."

    def _chapterize_text(self, text: str, min_chapter_length_sentences=20) -> List[str]:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        if not sentences:
            return [text]

        chapters = []
        current_chapter = []
        for sentence in sentences:
            is_heading = bool(
                re.match(r"^(CHAPTER|SECTION)\s+\d+", sentence, re.IGNORECASE)
            ) or (
                sentence.isupper() and len(sentence.split()) < 10 and len(sentence) > 5
            )

            if is_heading and len(current_chapter) >= min_chapter_length_sentences:
                chapters.append(" ".join(current_chapter))
                current_chapter = [sentence]
            else:
                current_chapter.append(sentence)

        if current_chapter:
            chapters.append(" ".join(current_chapter))

        return chapters if chapters else [text]

    def _assemble_audio_chapters(
        self, chapter_audio_segments: List[AudioSegment]
    ) -> bytes:
        full_audio = sum(chapter_audio_segments, AudioSegment.empty())

        audio_buffer = io.BytesIO()
        full_audio.export(audio_buffer, format="mp3")
        return audio_buffer.getvalue()
