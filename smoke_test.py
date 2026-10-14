
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    raise RuntimeError("API key not found in .env")

client = genai.Client(api_key=api_key)

try:
    response = client.interactions.create(
        model="gemini-3.8-flash",
        input="Reply with exactly: API connection works.",
    )
    print("Gemini API call successful!")
    print(response.output_text)

except Exception as exc:
    print(f"Gemini API call failed: {type(exc).__name__}")
    print(str(exc)[:500])
