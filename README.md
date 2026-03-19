# AI Interview Assistant

A real-time AI interview assistant built with Python and CustomTkinter. It listens to your microphone, transcribes the conversation using OpenAI Whisper, and generates suggested responses for interview questions using OpenAI GPT models.

## Features
- Real-time Speech-to-Text using OpenAI Whisper.
- Context-aware interview answers using OpenAI GPT-3.5-Turbo.
- Modern GUI with dark/light mode support using CustomTkinter.

## Prerequisites
- Python 3.10+
- PortAudio (for PyAudio)
- OpenAI API Key

## Installation
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create a `.env` file in the root directory and add your API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage
Run the application:
```bash
python src/main.py
```

## Build Executable
A GitHub Action is configured to automatically build a Windows `.exe` using PyInstaller upon push to the `main` branch.
