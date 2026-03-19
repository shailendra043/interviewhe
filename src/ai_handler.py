import os
from openai import OpenAI
import io

class AIHandler:
    def __init__(self, api_key=None):
        key = api_key or os.environ.get("OPENAI_API_KEY")
        base_url = "https://openrouter.ai/api/v1" if (key and key.startswith("sk-or-")) else None
        self.client = OpenAI(api_key=key, base_url=base_url)
        self.system_prompt = (
            "You are an expert AI interview assistant. "
            "You will be given a transcript of an interview question or discussion. "
            "Provide a concise, excellent answer or talking point to help the interviewee. "
            "Keep the response professional, directly addressing the prompt, and relatively short (2-4 sentences)."
        )
        self.context = []

    def set_api_key(self, api_key):
        self.client = OpenAI(api_key=api_key)

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
            self.context.append({"role": "user", "content": text})
            if len(self.context) > 10:
                self.context = self.context[-10:]

    def generate_response_from_context(self):
        if not self.context:
            return None
            
        messages = [{"role": "system", "content": self.system_prompt}] + self.context
        try:
            model_name = "openai/gpt-3.5-turbo" if getattr(self.client, "base_url", None) and self.client.base_url.host == "openrouter.ai" else "gpt-3.5-turbo"
            response = self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=200,
                temperature=0.7
            )
            reply = response.choices[0].message.content
            self.context.append({"role": "assistant", "content": reply})
            return reply
        except Exception as e:
            print(f"LLM error: {e}")
            if "401" in str(e):
                return "Error: Your OpenRouter/OpenAI API key is invalid or unrecognized."
            return f"Error generating response: {e}"
