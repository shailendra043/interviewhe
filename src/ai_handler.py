import os
import google.generativeai as genai

class AIHandler:
    def __init__(self, api_key=None):
        key = api_key or os.environ.get("GOOGLE_API_KEY")
        genai.configure(api_key=key)
        # Gemini 1.5 Flash is Google's incredibly fast, multimodal default model 
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        self.system_prompt = (
            "You are an expert AI interview assistant. "
            "You will be given a context log of an ongoing interview discussion. "
            "Provide a concise, excellent answer or talking point to help the interviewee. "
            "Keep the response professional, directly addressing the prompt, and relatively short (2-4 sentences)."
        )
        # We will hold dialogue context as a raw transcript block 
        self.context_transcript = ""
        # We will store attached PIL images for multimodal contexts
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
            # Truncate context if it gets absurdly long (keep last ~3000 chars)
            if len(self.context_transcript) > 3000:
                self.context_transcript = "..." + self.context_transcript[-3000:]

    def add_image(self, image):
        self.context_images.append(image)

    @property
    def context(self):
        return self.context_transcript.strip()
        
    @context.setter
    def context(self, value):
        # For main.py clear_text backwards compat
        if not value:
            self.context_transcript = ""
            self.context_images.clear()

    def generate_response_from_context(self):
        # Require either text context or images
        if not self.context_transcript.strip() and not self.context_images:
            return None
            
        prompt = f"{self.system_prompt}\n\nInterview Context:\n{self.context_transcript}\n\nProvide the best answer/points for the interviewee now:"
        
        try:
            # Pass a list containing the prompt string and any attached images
            contents = [prompt] + self.context_images
            response = self.model.generate_content(contents)
            
            reply = response.text
            self.context_transcript += f"AI Advice: {reply}\n"
            
            # Clear images after sending so they don't bloat future non-vision calls
            self.context_images.clear()
            return reply
        except Exception as e:
            print(f"LLM error: {e}")
            return f"Error generating response: {e}"
