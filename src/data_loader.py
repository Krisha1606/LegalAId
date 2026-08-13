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
    path = Path(file_path) if file_path is not None else Path(config.DATA_PATH)

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
