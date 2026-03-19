import customtkinter as ctk
import threading
import time
import os
from dotenv import load_dotenv

# Adjust imports for local modules
try:
    from audio_handler import AudioHandler
    from ai_handler import AIHandler
except ImportError:
    from src.audio_handler import AudioHandler
    from src.ai_handler import AIHandler

ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class InterviewAssistantApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AI Interview Assistant")
        self.geometry("800x600")
        self.minsize(600, 500)

        # Load Environment Variables
        load_dotenv()
        
        # App Logic Variables
        self.is_listening = False
        self.audio_handler = None
        self.ai_handler = None
        self.processing_thread = None
        
        # Setup UI
        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # Transcript expands
        self.grid_rowconfigure(4, weight=2) # AI Response expands more
        
        self.header = ctk.CTkLabel(self, text="Real-Time AI Interview Assistant", font=("Arial", 24, "bold"))
        self.header.grid(row=0, column=0, pady=10, padx=10, sticky="ew")
        
        self.transcript_label = ctk.CTkLabel(self, text="Live Transcript (You/Interviewer):", font=("Arial", 14, "bold"))
        self.transcript_label.grid(row=1, column=0, padx=10, sticky="w")
        
        self.transcript_box = ctk.CTkTextbox(self, font=("Arial", 14))
        self.transcript_box.grid(row=2, column=0, pady=5, padx=10, sticky="nsew")
        self.transcript_box.insert("0.0", "Waiting for speech...\n")
        self.transcript_box.configure(state="disabled")
        
        self.ai_label = ctk.CTkLabel(self, text="AI Recommended Answers:", font=("Arial", 14, "bold"))
        self.ai_label.grid(row=3, column=0, padx=10, sticky="w")
        
        self.ai_box = ctk.CTkTextbox(self, font=("Arial", 16), text_color="#28A745")
        self.ai_box.grid(row=4, column=0, pady=5, padx=10, sticky="nsew")
        self.ai_box.insert("0.0", "AI responses will appear here...\n")
        self.ai_box.configure(state="disabled")
        
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.grid(row=5, column=0, pady=10, padx=10, sticky="ew")
        self.button_frame.grid_columnconfigure((0, 1), weight=1)
        
        self.toggle_btn = ctk.CTkButton(self.button_frame, text="Start Listening", command=self.toggle_listening, font=("Arial", 16, "bold"), height=40)
        self.toggle_btn.grid(row=0, column=0, padx=10, pady=10)
        
        self.clear_btn = ctk.CTkButton(self.button_frame, text="Clear Context", command=self.clear_text, font=("Arial", 14), height=40, fg_color="gray")
        self.clear_btn.grid(row=0, column=1, padx=10, pady=10)
        
        self.settings_frame = ctk.CTkFrame(self)
        self.settings_frame.grid(row=6, column=0, pady=5, padx=10, sticky="ew")
        self.settings_frame.grid_columnconfigure(1, weight=1)
        
        self.api_key_label = ctk.CTkLabel(self.settings_frame, text="OpenAI API Key:")
        self.api_key_label.grid(row=0, column=0, padx=10, pady=5)
        
        self.api_key_var = ctk.StringVar(value=os.environ.get("OPENAI_API_KEY", ""))
        self.api_key_entry = ctk.CTkEntry(self.settings_frame, textvariable=self.api_key_var, show="*")
        self.api_key_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.api_key_entry.bind("<FocusOut>", self.save_api_key)

    def save_api_key(self, event=None):
        key = self.api_key_var.get().strip()
        if key:
            os.environ["OPENAI_API_KEY"] = key
            with open(".env", "w") as f:
                f.write(f"OPENAI_API_KEY={key}\n")
            if self.ai_handler:
                self.ai_handler.set_api_key(key)

    def toggle_listening(self):
        if not self.is_listening:
            self.start_listening()
        else:
            self.stop_listening()

    def start_listening(self):
        if not self.api_key_var.get().strip():
            self.append_text(self.ai_box, "\n[System] Error: Please enter your OpenAI API Key below.\n")
            return
            
        try:
            self.save_api_key() # Ensure key is saved
            
            if not self.audio_handler:
                self.audio_handler = AudioHandler()
            if not self.ai_handler:
                self.ai_handler = AIHandler()
                
            self.audio_handler.start_listening()
            self.is_listening = True
            self.toggle_btn.configure(text="Stop Listening", fg_color="#E74C3C", hover_color="#C0392B")
            
            # Start processing thread
            self.processing_thread = threading.Thread(target=self.process_audio_loop, daemon=True)
            self.processing_thread.start()
            
            self.append_text(self.transcript_box, "\n[System] Listening to microphone...\n")
        except Exception as e:
            self.append_text(self.transcript_box, f"\n[Error] {str(e)}\n")

    def stop_listening(self):
        if self.audio_handler:
            self.audio_handler.stop_listening()
        self.is_listening = False
        self.toggle_btn.configure(text="Start Listening", fg_color=["#3B8ED0", "#1F6AA5"], hover_color=["#36719F", "#144870"])
        self.append_text(self.transcript_box, "\n[System] Stopped listening.\n")

    def process_audio_loop(self):
        while self.is_listening:
            audio_data = self.audio_handler.get_audio_data()
            if audio_data:
                # Transcribe chunk
                transcript = self.ai_handler.transcribe_audio(audio_data)
                if transcript and len(transcript.strip()) > 5:
                    self.append_text(self.transcript_box, f"Speech: {transcript}\n")
                    
                    # Generate Answer
                    self.append_text(self.ai_box, "\nAI: Thinking...\n")
                    answer = self.ai_handler.generate_response(transcript)
                    
                    if answer:
                        self.remove_last_line(self.ai_box)
                        self.append_text(self.ai_box, f"\nAI: {answer}\n")
                    else:
                        self.remove_last_line(self.ai_box)
            else:
                time.sleep(0.1)

    def append_text(self, widget, text):
        widget.configure(state="normal")
        widget.insert("end", text)
        widget.see("end")
        widget.configure(state="disabled")

    def remove_last_line(self, widget):
        widget.configure(state="normal")
        widget.delete("end-2l", "end-1l")
        widget.configure(state="disabled")

    def clear_text(self):
        self.transcript_box.configure(state="normal")
        self.transcript_box.delete("0.0", "end")
        self.transcript_box.configure(state="disabled")
        self.ai_box.configure(state="normal")
        self.ai_box.delete("0.0", "end")
        self.ai_box.configure(state="disabled")
        if self.ai_handler:
            self.ai_handler.context = []

if __name__ == "__main__":
    app = InterviewAssistantApp()
    app.mainloop()
