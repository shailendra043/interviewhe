import os
from openai import OpenAI

key = "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"
client = OpenAI(api_key=key, base_url="https://openrouter.ai/api/v1")
try:
    response = client.chat.completions.create(
        model="openai/gpt-3.5-turbo",
        messages=[{"role": "user", "content": "hello"}]
    )
    print("Success:", response.choices[0].message.content)
except Exception as e:
    print("Error:", e)
