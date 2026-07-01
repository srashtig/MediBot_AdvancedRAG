"""Groq chat model setup."""

import getpass
import os

from langchain_groq import ChatGroq

from config import GROQ_KEY_FILE, GROQ_MODEL


def load_groq_api_key(key_file=GROQ_KEY_FILE):
    """Read the Groq API key from a text file if it exists."""
    if not key_file.exists():
        return None

    api_key = key_file.read_text().strip()
    return api_key or None


def get_llm():
    """Create the Groq chat model used by RAG and SQL chains."""
    if "GROQ_API_KEY" not in os.environ:
        api_key = load_groq_api_key()
        if api_key is None:
            api_key = getpass.getpass("Enter your Groq API key: ")
        os.environ["GROQ_API_KEY"] = api_key

    return ChatGroq(
        model=GROQ_MODEL,
        temperature=0,
        max_tokens=None,
        reasoning_format="parsed",
        timeout=None,
        max_retries=2,
    )
