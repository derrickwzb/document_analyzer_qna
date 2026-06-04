from dotenv import load_dotenv
import os
import sys

load_dotenv()
# --- CONFIGURATION & SECURITY GATEKEEPER ---
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    raise ValueError(
        "GROQ_API_KEY not found!\n"
        "Set it in your terminal:\n"
        "  macOS/Linux: export GROQ_API_KEY='your-key-here'\n"
        "  Windows CMD: set GROQ_API_KEY=your-key-here\n"
        "  Windows PS:  $env:GROQ_API_KEY='your-key-here'\n"
        "Or create a .env file with: GROQ_API_KEY=your-key-here"
    )

PDF_PATH = "sample.pdf"
# MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.0-flash")
# DB_NAME = os.getenv("DB_NAME", "summaries.db")

# if not GROQ_API_KEY:
#     sys.exit(1)
