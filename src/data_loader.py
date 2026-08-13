import json
from pathlib import Path
from typing import Any

from src.config import config


def load_raw_legal_data(
    file_path: str | Path | None = None,
) -> list[dict[str, Any]]:
    """Loads raw legal documents from a JSON file.

    Args:
        file_path: Path to the JSON file. Defaults to config.DATA_PATH.

    Returns:
        A list of raw dictionary records.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If the file is malformed JSON, empty, or has an invalid structure.
    """
    if file_path is not None:
        path = Path(file_path)
    elif config.DATA_PATH.is_file():
        path = config.DATA_PATH
    else:
        path = config.DUMMY_DATA_PATH

    if not path.is_file():
        raise FileNotFoundError(f"Legal dataset file not found at: {path.resolve()}")

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to parse JSON legal dataset at {path.resolve()}: {exc}") from exc
    except Exception as exc:
        raise ValueError(f"Unexpected error reading file at {path.resolve()}: {exc}") from exc

    records: list[dict[str, Any]]
    if isinstance(data, list):
        records = data
    elif isinstance(data, dict):
        if "documents" in data and isinstance(data["documents"], list):
            records = data["documents"]
        elif "records" in data and isinstance(data["records"], list):
            records = data["records"]
        else:
            raise ValueError(
                f"JSON object at {path.resolve()} does not contain a list of records under 'documents' or 'records'."
            )
    else:
        raise TypeError(
            f"Expected JSON array or dict at root of dataset, got {type(data).__name__}."
        )

    if not records:
        raise ValueError(f"Legal dataset at {path.resolve()} contains no records.")

    return records


def load_pdf_text(file_path: str | Path) -> str:
    """Extracts raw text from an official legal PDF document.

    Args:
        file_path: Path to the PDF file.

    Returns:
        Extracted text as a string.

    Raises:
        FileNotFoundError: If the PDF file is missing.
        ValueError: If extraction fails or yields no text.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"PDF file not found at: {path.resolve()}")

    try:
        import pypdf

        reader = pypdf.PdfReader(path)
        pages_text = []
        for page in reader.pages:
            txt = page.extract_text()
            if txt:
                pages_text.append(txt)
        full_text = "\n".join(pages_text)
    except Exception as exc:
        raise ValueError(f"Failed to extract text from PDF at {path.resolve()}: {exc}") from exc

    if not full_text.strip():
        raise ValueError(f"PDF at {path.resolve()} contained no readable text.")

    return full_text
