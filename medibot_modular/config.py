"""Shared configuration constants for MediBot."""

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = BASE_DIR.parent
DIR = BASE_DIR / "mediassist_data"
VECTORSTORE_PATH = BASE_DIR / "my_lang_vs"
DB_PATH = DIR / "db" / "mediassist.db"
GROQ_KEY_FILE = WORKSPACE_DIR / "groq_key.txt"

COLLECTION_DIRS = ["general", "clinical", "nursing", "billing", "equipment"]
ALL_ROLES = ["doctor", "nurse", "admin", "billing_executive", "technician"]

ACCESS_ROLES = {
    "general": ALL_ROLES,
    "clinical": ["doctor", "admin"],
    "nursing": ["nurse", "doctor", "admin"],
    "billing": ["billing_executive", "admin"],
    "equipment": ["technician", "admin"],
}

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
SPARSE_MODEL = "Qdrant/bm25"
GROQ_MODEL = "openai/gpt-oss-20b"
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
QDRANT_COLLECTION = "medibot"
