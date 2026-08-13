import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# Set Hugging Face cache directory to D: drive workspace storage/hf_cache to prevent C: drive disk space issues
hf_cache_dir = Path(os.getenv("HF_HOME", "storage/hf_cache")).resolve()
hf_cache_dir.mkdir(parents=True, exist_ok=True)
os.environ["HF_HOME"] = str(hf_cache_dir)
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"


@dataclass
class Config:
    """System configuration loaded from environment variables."""

    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
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
