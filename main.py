import os
from mistralai.client import Mistral
from src.prompts import system_prompt
from src.models import ESRSResponse

import re
import json

def clean_markdown(md: str) -> str:
    # remove code blocks
    md = re.sub(r"```.*?```", "", md, flags=re.DOTALL)
    
    # normalize quotes
    md = md.replace('"', "'")
    
    # collapse excessive whitespace
    md = re.sub(r"\n{3,}", "\n\n", md)
    
    return md

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

# ---- Read user content from markdown ----
# Prefer DATA_FOLDER/input.md if DATA_FOLDER is set; otherwise fall back to repo-relative data/input.md
_data_folder = os.getenv("DATA_FOLDER")
if _data_folder:
    input_path = os.path.join(_data_folder, "input.md")
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(base_dir, "data", "input.md")

if not os.path.isfile(input_path):
    raise RuntimeError(f"Input markdown file not found: {input_path}")

with open(input_path, "r", encoding="utf-8") as f:
    user_text = f.read()

user_text = clean_markdown(user_text)


# ---- Call Mistral with structured output ----
chat_response = client.chat.parse(
    model=model,
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_text},
    ],
    response_format=ESRSResponse,   # 👈 structured output schema
    max_tokens=10000,
    temperature=0
)

# ---- Parsed result ----
result: ESRSResponse = chat_response.choices[0].message.parsed

# Envelope: { "<stem>.json": [ {item...}, ... ] }
stem = os.path.splitext(os.path.basename(input_path))[0]
output_key = f"{stem}.json"
items = [i.model_dump() for i in result.items]
payload = {output_key: items}

# Ensure output directory exists and write file
base_dir = os.path.dirname(os.path.abspath(__file__))
out_dir = os.path.join(base_dir, "data")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "output.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)

print(f"Wrote output to {out_path}")
print(f"Key: {output_key} | Items: {len(items)}")

