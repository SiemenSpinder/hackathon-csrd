import os
from mistralai.client import Mistral
from src.prompts import system_prompt, user_text
from src.models import ESRSResponse


# Load environment variables from .env if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Read API key from environment
api_key = os.getenv("MISTRAL_API_KEY") or os.getenv("API_KEY")
if not api_key:
    raise RuntimeError("Missing API key: set MISTRAL_API_KEY or API_KEY in a .env file or environment variables.")

# ---- Setup client ----
model = "mistral-small-latest"

client = Mistral(api_key=api_key)


# ---- Call Mistral with structured output ----
chat_response = client.chat.parse(
    model=model,
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_text},
    ],
    response_format=ESRSResponse,   # 👈 structured output schema
    max_tokens=1024,
    temperature=0
)

# ---- Parsed result ----
result: ESRSResponse = chat_response.choices[0].message.parsed

# ---- Print structured output ----
for r in result.results:
    print("\n---")
    print("Code:", r.code)
    print("Status:", r.status)
    print("Confidence:", r.confidence)
    print("Justification:", r.justification)
    print("Evidence:", r.evidence)
