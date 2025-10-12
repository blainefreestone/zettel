import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- API Configuration ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MAX_RETRIES = 3
# Note: Model, temp, and tokens are now controlled by your prompt configuration in OpenAI
# so we can remove them from here.

# --- File & Directory Paths ---
# (This section remains unchanged)
OUTPUT_DIR = "zettel_output"
TEMPLATE_DIR = "templates"
PDF_IMAGE_DIR = os.path.join(OUTPUT_DIR, "images")
STRUCTURED_JSON_PATH = os.path.join(OUTPUT_DIR, "1_structured_annotations.json")
TRANSCRIBED_JSON_PATH = os.path.join(OUTPUT_DIR, "2_transcribed_annotations.json")
ORGANIZED_JSON_PATH = os.path.join(OUTPUT_DIR, "3_organized_ideas.json")
LITERATURE_NOTE_PATH = os.path.join(OUTPUT_DIR, "literature_note.md")
PERMANENT_NOTE_DIR = os.path.join(OUTPUT_DIR, "permanent_notes")

# --- Prompts ---
# IDs for pre-configured prompts in the OpenAI platform (for the 'responses' API).
# 🛑 Replace these placeholder IDs with the actual IDs from your OpenAI account.
TRANSCRIPTION_PROMPT_ID = "pmpt_68e5339340848196a8eeae5a06637a4203d8092be659d4f3"
ORGANIZATION_PROMPT_ID = "pmpt_68e3e5b36e088197b32b60758b7d33fe0a517e452586bc41"