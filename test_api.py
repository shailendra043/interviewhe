import os
from openai import OpenAI

key = "AIzaSyBlLCx-IC0rGvBj5u4uS6v0FZliJHi09m4"
client = OpenAI(api_key=key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
try:
    response = client.chat.completions.create(
        model="gemini-1.5-flash",
        messages=[{"role": "user", "content": "hello"}]
    )
    print("Success:", response.choices[0].message.content)
except Exception as e:
    print("Error:", e)
