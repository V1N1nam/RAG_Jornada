import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
MOCK_DIR = DATA_DIR / "mock"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
USE_REAL_API = os.getenv("USE_REAL_API", "true").lower() == "true"

VECTORSTORE_PATH = BASE_DIR / os.getenv(
    "VECTORSTORE_PATH",
    "data/vectorstore/faiss_index"
)