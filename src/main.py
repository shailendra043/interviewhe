import customtkinter as ctk
import threading
import time
import ctypes

try:
    from audio_handler import AudioHandler
    from ai_handler import AIHandler
except ImportError:
    from src.audio_handler import AudioHandler
    from src.ai_handler import AIHandler

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# Hardcoded API Key
API_KEY = "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"

class InterviewAssistantApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AI Interview Assistant")
        self.geometry("800x600")
        self.minsize(600, 500)

        # Hide from Taskbar
        self.attributes('-toolwindow', True)
        self.wm_attributes("-topmost", True)

        # App Logic Variables
        self.is_listening = False
        self.audio_handler = None
        self.ai_handler = None
        self.processing_thread = None
        
        self.setup_ui()
        
        # Hide from Screen Share
        self.hide_from_screen_sharing()

    def hide_from_screen_sharing(self):
        try:
            HWND = ctypes.windll.user32.GetParent(self.winfo_id())
            # Windows 10 v2004+ invisibility from screen capture: WDA_EXCLUDEFROMCAPTURE = 0x11
            # Fallback to WDA_MONITOR = 0x01 which makes it a black box
            result = ctypes.windll.user32.SetWindowDisplayAffinity(HWND, 0x11)
            if not result:
                ctypes.windll.user32.SetWindowDisplayAffinity(HWND, 0x01)
        except Exception as e:
            print(f"Could not modify display affinity: {e}")

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(4, weight=2)
        
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

    def toggle_listening(self):
        if not self.is_listening:
            self.start_listening()
        else:
            self.stop_listening()

    def start_listening(self):
        try:
            if not self.audio_handler:
                self.audio_handler = AudioHandler()
            if not self.ai_handler:
                self.ai_handler = AIHandler(api_key=API_KEY)
                
            self.audio_handler.start_listening()
            self.is_listening = True
            self.toggle_btn.configure(text="Stop Listening", fg_color="#E74C3C", hover_color="#C0392B")
            
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
                transcript = self.ai_handler.transcribe_audio(audio_data)
                if transcript and len(transcript.strip()) > 5:
                    self.append_text(self.transcript_box, f"Speech: {transcript}\n")
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
