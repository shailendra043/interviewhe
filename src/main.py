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

# Hardcoded API Key
API_KEY = "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"

class FloatingWidgetApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Determine sizes
        width = 850
        height = 450
        
        self.title("Whis-AI")
        self.geometry(f"{width}x{height}")
        
        # Security and Stealth modes
        self.attributes('-alpha', 0.95)
        self.wm_attributes("-topmost", True)
        self.configure(fg_color="#080C14") # Deep space background
        
        # Try to make it frameless but keep dragging functionality
        self.overrideredirect(True)
        
        # Settings for dragging
        self._offsetx = 0
        self._offsety = 0

        # Privacy display affinity
        self.hide_from_screen_sharing()

        # State variables
        self.is_listening = False
        self.audio_handler = None
        self.ai_handler = None
        self.processing_thread = None
        
        self.setup_ui()
        self.bind_shortcuts()

    def hide_from_screen_sharing(self):
        try:
            HWND = ctypes.windll.user32.GetParent(self.winfo_id())
            result = ctypes.windll.user32.SetWindowDisplayAffinity(HWND, 0x11)
            if not result:
                ctypes.windll.user32.SetWindowDisplayAffinity(HWND, 0x01)
        except Exception:
            pass

    def click_window(self, event):
        self._offsetx = event.x
        self._offsety = event.y
        
    def drag_window(self, event):
        x = self.winfo_pointerx() - self._offsetx
        y = self.winfo_pointery() - self._offsety
        self.geometry(f"+{x}+{y}")

    def setup_ui(self):
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)
        
        # ----------------------------------------------------------------------------------------
        # Top Custom Title Bar
        # ----------------------------------------------------------------------------------------
        self.title_bar = ctk.CTkFrame(self, fg_color="#111823", corner_radius=0, height=45)
        self.title_bar.grid(row=0, column=0, sticky="ew")
        self.title_bar.bind("<Button-1>", self.click_window)
        self.title_bar.bind("<B1-Motion>", self.drag_window)
        
        self.title_bar.grid_columnconfigure(1, weight=1)
        
        # Logo/Title
        self.logo_label = ctk.CTkLabel(self.title_bar, text="⚡ Whis-AI", font=("Segoe UI", 18, "bold"), text_color="#00E5FF")
        self.logo_label.grid(row=0, column=0, padx=20, pady=10)
        self.logo_label.bind("<Button-1>", self.click_window)
        self.logo_label.bind("<B1-Motion>", self.drag_window)
        
        # Center Shortcuts
        shortcuts_text = "Ctrl + \\ Hide      Ctrl + K Mic      Ctrl + Enter Send      Alt + Arrows Move"
        self.shortcuts_label = ctk.CTkLabel(self.title_bar, text=shortcuts_text, font=("Segoe UI", 12), text_color="#30BCAE")
        self.shortcuts_label.grid(row=0, column=1, pady=10)
        self.shortcuts_label.bind("<Button-1>", self.click_window)
        self.shortcuts_label.bind("<B1-Motion>", self.drag_window)
        
        # Profile/Close Icons (Mocked with unicode or text)
        self.close_btn = ctk.CTkButton(self.title_bar, text="✖", font=("Arial", 16), width=35, height=35, 
                                       fg_color="transparent", hover_color="#E74C3C", text_color="#637C94", command=self.exit_app)
        self.close_btn.grid(row=0, column=2, padx=10)
        
        # ----------------------------------------------------------------------------------------
        # Main View Area
        # ----------------------------------------------------------------------------------------
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=25, pady=15)
        self.main_frame.grid_rowconfigure((0, 1), weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)
        
        self.transcript_box = ctk.CTkTextbox(self.main_frame, fg_color="#0F1621", text_color="#8CA3B8", 
                                             font=("Segoe UI", 14), corner_radius=10, border_color="#1A2536", border_width=1)
        self.transcript_box.grid(row=0, column=0, columnspan=2, sticky="nsew", pady=(0, 10))
        self.transcript_box.insert("0.0", "Wait for mic or type text below...\n")
        self.transcript_box.configure(state="disabled")
        
        self.ai_box = ctk.CTkTextbox(self.main_frame, fg_color="#111D28", text_color="#00E5FF", 
                                     font=("Segoe UI", 16, "bold"), corner_radius=10, border_color="#1A2536", border_width=1)
        self.ai_box.grid(row=1, column=0, columnspan=2, sticky="nsew")
        self.ai_box.insert("0.0", "Ready.\n")
        self.ai_box.configure(state="disabled")
        
        # ----------------------------------------------------------------------------------------
        # Bottom Input Area
        # ----------------------------------------------------------------------------------------
        self.bottom_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_bar.grid(row=2, column=0, sticky="ew", padx=25, pady=(0, 20))
        self.bottom_bar.grid_columnconfigure(2, weight=1)
        
        # Mic
        self.mic_btn = ctk.CTkButton(self.bottom_bar, text="🎙️", font=("Segoe UI", 20), width=50, height=45, 
                                     fg_color="#212E41", hover_color="#304058", corner_radius=12, command=self.toggle_mic)
        self.mic_btn.grid(row=0, column=0, padx=(0, 10))
        
        # Camera (Snap) - Visual placeholder
        self.cam_btn = ctk.CTkButton(self.bottom_bar, text="📷", font=("Segoe UI", 18), width=50, height=45, 
                                     fg_color="#212E41", hover_color="#304058", corner_radius=12)
        self.cam_btn.grid(row=0, column=1, padx=(0, 10))
        
        # Input Entry
        self.input_parent = ctk.CTkFrame(self.bottom_bar, fg_color="#0B111A", corner_radius=20, border_width=1, border_color="#1C2A3C")
        self.input_parent.grid(row=0, column=2, sticky="ew", padx=(0, 10))
        self.input_parent.grid_columnconfigure(0, weight=1)
        self.input_parent.grid_rowconfigure(0, weight=1)
        
        self.input_entry = ctk.CTkEntry(self.input_parent, placeholder_text="Type or use mic...", font=("Segoe UI", 14), 
                                        height=45, fg_color="transparent", border_width=0, text_color="#FFFFFF")
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=15)
        
        # Send Action
        self.send_btn = ctk.CTkButton(self.bottom_bar, text="➤", font=("Arial", 20, "bold"), width=50, height=45, 
                                      fg_color="#00E5FF", hover_color="#00BCCC", text_color="#000000", corner_radius=12, command=self.send_text)
        self.send_btn.grid(row=0, column=3)
        
    def bind_shortcuts(self):
        self.bind("<Control-backslash>", lambda e: self.toggle_visibility())
        self.bind("<Control-k>", lambda e: self.toggle_mic())
        self.bind("<Control-Return>", lambda e: self.send_text())

    def exit_app(self):
        if self.audio_handler:
            self.audio_handler.stop_listening()
        self.destroy()

    def toggle_visibility(self):
        # For overrideredirect windows, state normal/iconic isn't standard, withdraw and deiconify work best
        if self.winfo_viewable():
            self.withdraw()
        else:
            self.deiconify()

    def toggle_mic(self):
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
            
            self.mic_btn.configure(fg_color="#00E5FF", text_color="#000000", hover_color="#00BCCC")
            self.append_text(self.transcript_box, "\n[System] Listening to audio...\n")
            
            self.processing_thread = threading.Thread(target=self.process_audio_loop, daemon=True)
            self.processing_thread.start()
        except Exception as e:
            self.append_text(self.transcript_box, f"\n[Error] {str(e)}\n")

    def stop_listening(self):
        if self.audio_handler:
            self.audio_handler.stop_listening()
        self.is_listening = False
        self.mic_btn.configure(fg_color="#212E41", hover_color="#304058", text_color="#DCE4EE")
        self.append_text(self.transcript_box, "\n[System] Stopped listening.\n")

    def send_text(self):
        user_text = self.input_entry.get().strip()
        if user_text:
            self.input_entry.delete(0, 'end')
            if not self.ai_handler:
                self.ai_handler = AIHandler(api_key=API_KEY)
            self.append_text(self.transcript_box, f"User Typed: {user_text}\n")
            self.append_text(self.ai_box, "\nAI Analyzing...\n")
            threading.Thread(target=self._process_text, args=(user_text,), daemon=True).start()

    def _process_text(self, text):
        answer = self.ai_handler.generate_response(text)
        self.remove_last_line(self.ai_box)
        if answer:
            self.append_text(self.ai_box, f"\n[AI] {answer}\n")

    def process_audio_loop(self):
        while self.is_listening:
            audio_data = self.audio_handler.get_audio_data()
            if audio_data:
                transcript = self.ai_handler.transcribe_audio(audio_data)
                if transcript and len(transcript.strip()) > 5:
                    self.append_text(self.transcript_box, f"Audio: {transcript}\n")
                    self.append_text(self.ai_box, "\nAI Analyzing...\n")
                    
                    answer = self.ai_handler.generate_response(transcript)
                    self.remove_last_line(self.ai_box)
                    if answer:
                        self.append_text(self.ai_box, f"\n[AI] {answer}\n")
            else:
                time.sleep(0.1)

    def append_text(self, widget, text):
        widget.configure(state="normal")
        widget.insert("end", text)
        widget.see("end")
        widget.configure(state="disabled")

    def remove_last_line(self, widget):
        widget.configure(state="normal")
        # Delete the line "\nAI Analyzing...\n" plus the lines around it created during insert
        widget.delete("end-2l", "end-1l")
        widget.configure(state="disabled")

if __name__ == "__main__":
    app = FloatingWidgetApp()
    app.mainloop()
