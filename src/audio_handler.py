import queue
import threading
import sys

try:
    import pyaudiowpatch as pyaudio
    # Monkey-patch sys.modules so speech_recognition finds PyAudio
    sys.modules['pyaudio'] = pyaudio
except ImportError:
    import pyaudio

import speech_recognition as sr

class MonoStreamWrapper:
    def __init__(self, stream, channels):
        self.stream = stream
        self.channels = channels
        
    def read(self, size, exception_on_overflow=False):
        # PyAudio WPatch ignores exception_on_overflow in some versions so we catch carefully
        try:
            data = self.stream.read(size, exception_on_overflow=exception_on_overflow)
        except Exception:
            data = self.stream.read(size, exception_on_overflow=False)
            
        if self.channels > 1:
            try:
                import numpy as np
                arr = np.frombuffer(data, dtype=np.int16)
                arr = arr.reshape(-1, self.channels)
                return arr.mean(axis=1).astype(np.int16).tobytes()
            except ImportError:
                import audioop
                return audioop.tomono(data, 2, 0.5, 0.5)
        return data
        
    def close(self):
        self.stream.close()
        
    def stop_stream(self):
        self.stream.stop_stream()

class LoopbackMicrophone(sr.Microphone):
    def __init__(self, device_index, sample_rate, channels):
        super().__init__(device_index=device_index, sample_rate=sample_rate)
        self.channels = channels

    def __enter__(self):
        assert self.stream is None, "This audio source is already inside a context manager"
        self.audio = self.pyaudio_module.PyAudio()
        try:
            self.stream = self.audio.open(
                input_device_index=self.device_index,
                channels=self.channels,
                format=self.format, 
                rate=self.SAMPLE_RATE, 
                frames_per_buffer=self.CHUNK,
                input=True,
                as_loopback=True
            )
            # Wrap the stream so SpeechRecognition only sees Mono audio, otherwise WASAPI stereo breaks Google Speech 
            self.stream = MonoStreamWrapper(self.stream, self.channels)
        except Exception as e:
            self.audio.terminate()
            self.stream = None
            raise ValueError(f"Loopback setup failed: {e}")
        return self

class AudioHandler:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.stop_listening_func = None
        
        device_index = None
        channels = 2
        rate = 44100
        
        try:
            p = pyaudio.PyAudio()
            if hasattr(p, 'get_loopback_device_info_generator'):
                default_speakers = p.get_default_output_device_info()
                for loopback in p.get_loopback_device_info_generator():
                    if default_speakers["name"] in loopback["name"]:
                        device_index = loopback["index"]
                        channels = int(loopback["maxInputChannels"])
                        rate = int(loopback["defaultSampleRate"])
                        break
        except Exception as e:
            print(f"Warning: Could not find loopback device: {e}")
            
        if device_index is not None:
            self.microphone = LoopbackMicrophone(device_index=device_index, sample_rate=rate, channels=channels)
        else:
            self.microphone = sr.Microphone()

        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
        except Exception as e:
            print(f"Audio init warning: {e}")

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
