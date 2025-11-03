import os
import tempfile
from typing import Optional, Callable
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import openai
from pydub import AudioSegment
import io
import re
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.units import inch

class PDFToAudioPipeline:
    def __init__(self):
        # Initialize OpenAI client
        openai.api_key = os.getenv('OPENAI_API_KEY')
        
        # Voice mapping
        self.voice_mapping = {
            "default": "alloy",
            "female": "nova", 
            "male": "onyx",
            "child": "shimmer"
        }
    
    def process_pdf(
        self, 
        pdf_path: str, 
        voice_type: str = "default",
        reading_speed: float = 1.0,
        include_summary: bool = False,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> bytes:
        """
        Convert PDF to audio using OCR and TTS
        """
        try:
            # Step 1: Extract text from PDF (10% progress)
            if progress_callback:
                progress_callback(10)
            
            text_content = self._extract_text_from_pdf(pdf_path)
            
            if not text_content.strip():
                raise ValueError("No text could be extracted from the PDF")
            
            # Step 2: Clean and structure text (20% progress)
            if progress_callback:
                progress_callback(20)
            
            cleaned_text = self._clean_text(text_content)
            
            # Step 3: Generate summary if requested (30% progress)
            if include_summary:
                if progress_callback:
                    progress_callback(30)
                
                summary = self._generate_summary(cleaned_text)
                full_text = f"Summary: {summary}\\n\\nFull text:\\n{cleaned_text}"
            else:
                full_text = cleaned_text
            
            # Step 4: Convert to SSML (40% progress)
            if progress_callback:
                progress_callback(40)
            
            ssml_content = self._text_to_ssml(full_text, reading_speed)
            
            # Step 5: Generate audio (50-90% progress)
            if progress_callback:
                progress_callback(50)
            
            audio_data = self._generate_audio_from_ssml(
                ssml_content, 
                self.voice_mapping.get(voice_type, "alloy"),
                progress_callback
            )
            
            # Step 6: Final processing (100% progress)
            if progress_callback:
                progress_callback(100)
            
            return audio_data
            
        except Exception as e:
            raise Exception(f"PDF processing failed: {str(e)}")
    
    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using OCR"""
        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=300)
            
            full_text = ""
            
            for i, image in enumerate(images):
                # Preprocess image for better OCR
                image = self._preprocess_image(image)
                
                # Extract text using Tesseract OCR
                text = pytesseract.image_to_string(image, lang='eng')
                full_text += text + "\\n"
            
            return full_text
            
        except Exception as e:
            raise Exception(f"Text extraction failed: {str(e)}")
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results"""
        # Convert to grayscale
        image = image.convert('L')
        
        # Increase contrast
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        
        # Resize for better OCR
        width, height = image.size
        image = image.resize((int(width * 1.5), int(height * 1.5)))
        
        return image
    
    def _clean_text(self, text: str) -> str:
        """Clean and structure extracted text"""
        # Remove extra whitespace
        text = re.sub(r'\\s+', ' ', text)
        
        # Fix common OCR errors
        text = text.replace('|', 'I')
        text = text.replace('0', 'O', text.count('0'))
        
        # Remove page numbers and headers/footers
        lines = text.split('\\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip likely page numbers
            if line.isdigit() or (len(line) < 5 and any(c.isdigit() for c in line)):
                continue
            # Skip very short lines (likely headers/footers)
            if len(line) < 3:
                continue
            cleaned_lines.append(line)
        
        return '\\n'.join(cleaned_lines)
    
    def _generate_summary(self, text: str) -> str:
        """Generate a summary of the text using OpenAI"""
        try:
            # Truncate text if too long
            max_text_length = 4000  # Leave room for summary
            if len(text) > max_text_length:
                text = text[:max_text_length] + "..."
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that creates concise summaries of text. Create a summary that is no more than 150 words."
                    },
                    {
                        "role": "user", 
                        "content": f"Please summarize this text:\\n\\n{text}"
                    }
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            # If summarization fails, return first paragraph as fallback
            paragraphs = text.split('\\n\\n')
            return paragraphs[0] if paragraphs else text[:200] + "..."
    
    def _text_to_ssml(self, text: str, reading_speed: float) -> str:
        """Convert text to SSML for better TTS"""
        # Split text into manageable chunks
        chunks = self._split_text_into_chunks(text, 3000)
        
        ssml_chunks = []
        for chunk in chunks:
            # Escape SSML special characters
            chunk = chunk.replace('&', '&amp;')
            chunk = chunk.replace('<', '&lt;')
            chunk = chunk.replace('>', '&gt;')
            chunk = chunk.replace('"', '&quot;')
            chunk = chunk.replace("'", '&apos;')
            
            # Add prosody for speed control
            rate = f"{reading_speed * 100:.0f}%"
            ssml = f'<speak><prosody rate="{rate}">{chunk}</prosody></speak>'
            ssml_chunks.append(ssml)
        
        return ssml_chunks
    
    def _split_text_into_chunks(self, text: str, max_length: int) -> list:
        """Split text into chunks that don't exceed max_length"""
        chunks = []
        sentences = text.split('. ')
        
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk + sentence) < max_length:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _generate_audio_from_ssml(
        self, 
        ssml_chunks: list, 
        voice: str,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> bytes:
        """Generate audio from SSML using OpenAI TTS"""
        try:
            audio_segments = []
            total_chunks = len(ssml_chunks)
            
            for i, ssml in enumerate(ssml_chunks):
                # Generate audio for this chunk
                response = openai.Audio.create(
                    model="tts-1",
                    voice=voice,
                    input=ssml.replace('<speak>', '').replace('</speak>', '').replace('<prosody rate="">', '').replace('</prosody>', '')
                )
                
                # Convert to AudioSegment
                audio_segment = AudioSegment.from_file(io.BytesIO(response['content']))
                audio_segments.append(audio_segment)
                
                # Update progress (50% + (i+1)/total_chunks * 40%)
                if progress_callback:
                    progress = 50 + int(((i + 1) / total_chunks) * 40)
                    progress_callback(progress)
            
            # Combine all audio segments
            if audio_segments:
                final_audio = sum(audio_segments)
                
                # Export as MP3
                audio_buffer = io.BytesIO()
                final_audio.export(audio_buffer, format="mp3", bitrate="128k")
                return audio_buffer.getvalue()
            
            raise Exception("No audio segments were generated")
            
        except Exception as e:
            raise Exception(f"Audio generation failed: {str(e)}")