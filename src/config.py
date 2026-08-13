import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()


@dataclass
class Config:
    """System configuration loaded from environment variables."""

    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    TOP_K: int = int(os.getenv("TOP_K", "5"))
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.35"))
    DATA_PATH: Path = Path(os.getenv("DATA_PATH", "data/legal_knowledge_base.json"))
    DUMMY_DATA_PATH: Path = Path(os.getenv("DUMMY_DATA_PATH", "data/dummy_legal_data.json"))
    RAW_PDF_DIR: Path = Path(os.getenv("RAW_PDF_DIR", "data/pdfs"))
    KNOWLEDGE_BASE_PATH: Path = Path(
        os.getenv("KNOWLEDGE_BASE_PATH", "data/legal_knowledge_base.json")
    )
    TEST_DATA_PATH: Path = Path(os.getenv("TEST_DATA_PATH", "data/dummy_test_queries.json"))
    VECTOR_STORE_PATH: Path = Path(os.getenv("VECTOR_STORE_PATH", "storage/legal_index"))


# Default global config instance
config = Config()
