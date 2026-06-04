from dotenv import load_dotenv
import os
import sys

load_dotenv()
# --- CONFIGURATION & SECURITY GATEKEEPER ---
api_key = os.environ.get("GROQ_API_KEY")
chroma_directory = os.environ.get("CHROMA_DIR")
chroma_collection = os.environ.get("COLLECTION_NAME")
db_name = os.getenv("DB_NAME", "history.db")

if not api_key:
    raise ValueError(
        "GROQ_API_KEY not found!\n"
        "Set it in your terminal:\n"
        "  macOS/Linux: export GROQ_API_KEY='your-key-here'\n"
        "  Windows CMD: set GROQ_API_KEY=your-key-here\n"
        "  Windows PS:  $env:GROQ_API_KEY='your-key-here'\n"
        "Or create a .env file with: GROQ_API_KEY=your-key-here"
    )

if not api_key:
    sys.exit(1)
