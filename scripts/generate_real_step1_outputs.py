import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import config
from src.data_loader import load_raw_legal_data
from src.normalizer import normalize_dataset


def main():
    output_dir = Path("test_outputs/real_data_step1")
    output_dir.mkdir(parents=True, exist_ok=True)

    kb_path = config.KNOWLEDGE_BASE_PATH
    print(f"Loading raw legal dataset from {kb_path.resolve()}...")
    raw_records = load_raw_legal_data(kb_path)
    raw_count = len(raw_records)

    print(f"Normalizing {raw_count} raw legal records...")
    normalized_docs = normalize_dataset(raw_records)
    normalized_count = len(normalized_docs)

    ids = [doc.id for doc in normalized_docs]
    unique_ids_count = len(set(ids))

    domains = Counter(doc.domain for doc in normalized_docs)
    acts = Counter(doc.act_name or doc.act for doc in normalized_docs)
    verified_status = Counter(doc.verified for doc in normalized_docs)

    missing_text = sum(1 for doc in normalized_docs if not doc.legal_text.strip())
    missing_act = sum(1 for doc in normalized_docs if not (doc.act_name or doc.act).strip())
    missing_section = sum(1 for doc in normalized_docs if not doc.section.strip())
    missing_source_url = sum(1 for doc in normalized_docs if not (doc.source_url or "").strip())

    summary = {
        "step": "real_data_step1_normalization",
        "dataset_path": str(kb_path.resolve()),
        "raw_record_count": raw_count,
        "normalized_record_count": normalized_count,
        "unique_document_ids_count": unique_ids_count,
        "validation_issues": {
            "missing_legal_text": missing_text,
            "missing_act": missing_act,
            "missing_section": missing_section,
            "missing_source_url": missing_source_url,
            "duplicate_document_ids": raw_count - unique_ids_count,
        },
        "domain_distribution": dict(domains),
        "act_distribution": dict(acts),
        "verification_status": dict(verified_status),
        "status": "SUCCESS"
        if (raw_count == normalized_count == unique_ids_count and missing_text == 0)
        else "FAILED",
    }

    json_path = output_dir / "normalization_summary.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    report_lines = [
        "=" * 80,
        "LEGAL AID REAL DATA STEP 1 & 2 NORMALIZATION VALIDATION REPORT",
        "=" * 80,
        f"Raw Records Loaded         : {raw_count}",
        f"Normalized Records         : {normalized_count}",
        f"Unique Document IDs        : {unique_ids_count}",
        f"Missing Legal Text         : {missing_text}",
        f"Missing Act Name           : {missing_act}",
        f"Missing Section            : {missing_section}",
        f"Missing Source URL         : {missing_source_url}",
        "-" * 80,
        "DOMAIN DISTRIBUTION:",
    ]
    for dom, cnt in domains.items():
        report_lines.append(f"  - {dom}: {cnt} records")

    report_lines.append("-" * 80)
    report_lines.append("ACT DISTRIBUTION:")
    for act, cnt in acts.items():
        report_lines.append(f"  - {act}: {cnt} records")

    report_lines.append("=" * 80)
    report_path = output_dir / "normalization_report.txt"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    print(f"Step 1 real data outputs saved successfully to {output_dir.resolve()}!")
    print(f"Status: {summary['status']}")


if __name__ == "__main__":
    main()
