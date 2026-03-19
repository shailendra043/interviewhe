import os
from openai import OpenAI
import io

class AIHandler:
    def __init__(self):
        # We expect the OPENAI_API_KEY environment variable to be set
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
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
        """Transcribe audio data using Whisper."""
        try:
            # audio_data is an sr.AudioData object
            wav_data = audio_data.get_wav_data()
            
            # OpenAI requires a file-like object with a name attribute
            audio_file = io.BytesIO(wav_data)
            audio_file.name = "audio.wav"
            
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file,
                language="en"
            )
            return transcript.text
        except Exception as e:
            print(f"Transcription error: {e}")
            return None

    def generate_response(self, transcript_text):
        """Generate response given a transcript segment."""
        if not transcript_text or len(transcript_text.strip()) < 10:
            # Ignore very short noises/words that probably aren't questions
            return None
            
        self.context.append({"role": "user", "content": transcript_text})
        
        # Keep context small to reduce token usage and latency (last 4 messages + system)
        if len(self.context) > 4:
            self.context = self.context[-4:]
            
        messages = [{"role": "system", "content": self.system_prompt}] + self.context
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=150,
                temperature=0.7
            )
            reply = response.choices[0].message.content
            self.context.append({"role": "assistant", "content": reply})
            return reply
        except Exception as e:
            print(f"LLM error: {e}")
            return "Error generating response."
