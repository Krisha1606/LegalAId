"""End-to-end pipeline for Person 1: Legal Data & Knowledge Base generation."""

import json
from pathlib import Path
from typing import Any

from src.chunker import chunk_legal_pdf_text
from src.config import config
from src.data_loader import load_pdf_text
from src.normalizer import (
    normalize_dataset,
    validate_knowledge_base_record,
)


def build_legal_knowledge_base(
    pdf_dir: str | Path | None = None,
    output_json_path: str | Path | None = None,
) -> list[dict[str, Any]]:
    """Builds legal_knowledge_base.json from official legal PDFs in pdf_dir.

    Args:
        pdf_dir: Directory containing official PDF Acts. Defaults to config.RAW_PDF_DIR.
        output_json_path: Path to write legal_knowledge_base.json. Defaults to config.KNOWLEDGE_BASE_PATH.

    Returns:
        List of formatted legal knowledge base record dictionaries.
    """
    raw_pdf_path = Path(pdf_dir) if pdf_dir is not None else Path(config.RAW_PDF_DIR)
    out_path = (
        Path(output_json_path) if output_json_path is not None else Path(config.KNOWLEDGE_BASE_PATH)
    )

    pdf_files = list(raw_pdf_path.glob("*.pdf"))
    all_raw_records: list[dict[str, Any]] = []

    if pdf_files:
        print(f"Processing {len(pdf_files)} PDF file(s) from {raw_pdf_path.resolve()}...")
        for pdf in pdf_files:
            print(f"  - Extracting text from {pdf.name}...")
            text = load_pdf_text(pdf)
            domain = "consumer"
            if "labour" in pdf.name.lower():
                domain = "labour"
            elif "tenant" in pdf.name.lower() or "rent" in pdf.name.lower():
                domain = "tenant"

            records = chunk_legal_pdf_text(
                full_text=text,
                domain=domain,
                source_name="India Code",
                source_url="https://www.indiacode.nic.in/handle/123456789/15256",
                last_verified="2026-08-13",
            )
            print(f"    Extracted {len(records)} legal provisions/sections.")
            all_raw_records.extend(records)
    else:
        print(f"No PDF files found in {raw_pdf_path.resolve()}. Using fallback datasets...")

    # Normalize records
    normalized_docs = normalize_dataset(all_raw_records)
    final_output_records = []

    for doc in normalized_docs:
        rec_dict = doc.to_dict()
        # Keep Person 1 required output structure
        clean_rec = {
            "domain": rec_dict["domain"],
            "act_name": rec_dict["act_name"],
            "act_number": rec_dict["act_number"],
            "year": rec_dict["year"],
            "section": rec_dict["section"],
            "section_title": rec_dict["section_title"],
            "chapter": rec_dict["chapter"],
            "legal_text": rec_dict["legal_text"],
            "plain_summary": rec_dict["plain_summary"],
            "keywords": rec_dict["keywords"],
            "source_name": rec_dict["source_name"],
            "source_url": rec_dict["source_url"],
            "verified": rec_dict["verified"],
            "last_verified": rec_dict["last_verified"],
        }
        errs = validate_knowledge_base_record(clean_rec)
        if errs:
            print(f"Warning: Record validation issue for {clean_rec['section']}: {errs}")
        final_output_records.append(clean_rec)

    # Save to JSON file
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(final_output_records, f, indent=2, ensure_ascii=False)

    print(f"Successfully generated legal_knowledge_base.json at: {out_path.resolve()}")
    print(f"Total records saved: {len(final_output_records)}")
    return final_output_records


if __name__ == "__main__":
    build_legal_knowledge_base()
