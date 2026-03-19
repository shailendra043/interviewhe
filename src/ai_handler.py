import os
import json
import urllib.request
import urllib.error
import base64
from io import BytesIO

class AIHandler:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        self.system_prompt = (
            "You are an expert AI interview assistant. "
            "You will be given a context log of an ongoing interview discussion. "
            "Provide a concise, excellent answer or talking point to help the interviewee. "
            "Keep the response professional, directly addressing the prompt, and relatively short (2-4 sentences)."
        )
        self.context_transcript = ""
        self.context_images = []

    def transcribe_audio(self, audio_data):
        """Transcribe audio data using Google Web Speech (Free & Compatible)."""
        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            transcript = recognizer.recognize_google(audio_data)
            return transcript
        except Exception as e:
            print(f"Transcription error: {e}")
            return None

    def add_to_context(self, text):
        if text and len(text.strip()) >= 5:
            self.context_transcript += f"{text}\n"
            if len(self.context_transcript) > 3000:
                self.context_transcript = "..." + self.context_transcript[-3000:]

    def add_image(self, image):
        self.context_images.append(image)

    @property
    def context(self):
        return self.context_transcript.strip()
        
    @context.setter
    def context(self, value):
        if not value:
            self.context_transcript = ""
            self.context_images.clear()

    def generate_response_from_context(self):
        if not self.context_transcript.strip() and not self.context_images:
            return None
            
        full_text_prompt = f"{self.system_prompt}\n\nInterview Context:\n{self.context_transcript}\n\nProvide the best answer/points for the interviewee now:"
        
        parts = [{"text": full_text_prompt}]
        
        for img in self.context_images:
            try:
                buffered = BytesIO()
                img.convert("RGB").save(buffered, format="JPEG")
                img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                parts.append({
                    "inlineData": {
                        "mimeType": "image/jpeg",
                        "data": img_str
                    }
                })
            except Exception as e:
                print(f"Image processing error: {e}")
                pass
            
        payload = {
            "contents": [
                {
                    "parts": parts
                }
            ]
        }
        
        req = urllib.request.Request(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent",
            data=json.dumps(payload).encode('utf-8'),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key
            },
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req) as response:
                response_data = json.loads(response.read().decode('utf-8'))
                reply = response_data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                
                if reply:
                    self.context_transcript += f"AI Advice: {reply}\n"
                    self.context_images.clear()
                    return reply.strip()
                return "Error: No text returned from API."
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode('utf-8')
            print(f"LLM REST HTTP Error: {err_msg}")
            return f"API Error: {err_msg}"
        except Exception as e:
            print(f"LLM REST error: {e}")
            return f"Error generating response: {e}"
