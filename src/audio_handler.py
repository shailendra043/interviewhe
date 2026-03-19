import speech_recognition as sr
import queue
import threading
import sys

try:
    import pyaudiowpatch as pyaudio
except ImportError:
    import pyaudio

class AudioHandler:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.stop_listening_func = None
        
        device_index = None
        
        # Attempt to find the WASAPI Loopback device for system audio
        try:
            p = pyaudio.PyAudio()
            if hasattr(p, 'get_loopback_device_info_generator'):
                default_speakers = p.get_default_output_device_info()
                for loopback in p.get_loopback_device_info_generator():
                    if default_speakers["name"] in loopback["name"]:
                        device_index = loopback["index"]
                        break
        except Exception as e:
            print(f"Warning: Could not find loopback device: {e}")
            
        if device_index is not None:
            self.microphone = sr.Microphone(device_index=device_index)
        else:
            self.microphone = sr.Microphone()

        # Adjust for ambient noise on initialization
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)

    def start_listening(self):
        if self.is_listening:
            return
        
        self.is_listening = True
        
        def callback(recognizer, audio):
            # audio is an sr.AudioData object
            self.audio_queue.put(audio)
            
        # listen_in_background spawns a thread to listen and calls the callback when a phrase is detected
        self.stop_listening_func = self.recognizer.listen_in_background(
            self.microphone, 
            callback,
            phrase_time_limit=10 # max 10 seconds per phrase to ensure real-time
        )

    def stop_listening(self):
        if not self.is_listening:
            return
        
        if self.stop_listening_func:
            self.stop_listening_func(wait_for_stop=False)
            
        self.is_listening = False
        self.stop_listening_func = None

    def get_audio_data(self):
        try:
            return self.audio_queue.get_nowait()
        except queue.Empty:
            return None
