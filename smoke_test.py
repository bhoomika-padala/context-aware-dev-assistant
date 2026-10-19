
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY"),
    timeout=20.0,
    max_retries=0,
)

try:
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "user",
                "content": "Reply with exactly: Groq generation works."
            }
        ],
        max_completion_tokens=100,
    )

    print("Generation successful!")
    print(response.choices[0].message.content)

except Exception as exc:
    print(f"Request failed: {type(exc).__name__}")
    print(str(exc)[:500])
