import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import config
from src.data_loader import load_raw_legal_data


def validate_raw_loading():
    print("=== LEGALAID REAL DATA RAW LOADING VALIDATION (PHASE 1) ===")
    
    # 1. Verify production path configuration
    prod_path = config.DATA_PATH
    print(f"Configured Production DATA_PATH: {prod_path}")
    print(f"Path exists: {prod_path.is_file()}")
    
    # 2. Load records via data_loader
    raw_records = load_raw_legal_data()
    total_loaded = len(raw_records)
    print(f"Loaded total raw records: {total_loaded}")
    
    # 3. Read directly from legal_knowledge_base.json to verify byte/content identity
    with open(prod_path, encoding="utf-8") as f:
        direct_raw = json.load(f)
    
    assert total_loaded == len(direct_raw), f"Record count mismatch: loader={total_loaded}, file={len(direct_raw)}"
    print(f"Raw record count match confirmed: {total_loaded} records.")
    
    # 4. Check domain counts
    domain_counts = {}
    missing_fields = {}
    
    # Define expected fields from Person 1 schema
    expected_fields = [
        "act_name",
        "section",
        "section_title",
        "legal_text",
        "plain_summary",
        "keywords",
        "source_name",
        "source_url",
        "domain",
        "issue",
        "jurisdiction",
        "applicability",
        "verified",
        "is_dummy",
    ]
    
    for f in expected_fields:
        missing_fields[f] = 0

    raw_text_matches = 0
    for idx, (loaded_rec, direct_rec) in enumerate(zip(raw_records, direct_raw)):
        # Domain count
        dom = loaded_rec.get("domain", "missing_domain")
        domain_counts[dom] = domain_counts.get(dom, 0) + 1
        
        # Missing fields check
        for field in expected_fields:
            if field not in loaded_rec or loaded_rec[field] is None:
                missing_fields[field] += 1
                
        # Text integrity check
        if loaded_rec.get("legal_text") == direct_rec.get("legal_text"):
            raw_text_matches += 1

    text_integrity_passed = (raw_text_matches == total_loaded)
    print(f"Domain breakdown: {domain_counts}")
    print(f"Missing fields breakdown: {missing_fields}")
    print(f"Legal text integrity match: {raw_text_matches}/{total_loaded} ({'PASSED' if text_integrity_passed else 'FAILED'})")
    
    # Print representative sample keys and metadata
    sample_rec = raw_records[0]
    print("\n--- Representative Record (Index 0) ---")
    print(f"Keys ({len(sample_rec.keys())}): {list(sample_rec.keys())}")
    print(f"Domain: {sample_rec.get('domain')}")
    print(f"Act: {sample_rec.get('act_name')}")
    print(f"Section: {sample_rec.get('section')}")
    print(f"Section Title: {sample_rec.get('section_title')}")
    print(f"Source URL: {sample_rec.get('source_url')}")
    print("---------------------------------------\n")
    
    # Prepare Phase 1 output report
    output_dir = Path("test_outputs/real_data_step1")
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "raw_loading_report.json"
    
    # Strip full text from sample_record in report to keep report clean while showing metadata
    sample_metadata = {k: v for k, v in sample_rec.items() if k not in ("legal_text", "plain_summary")}
    
    report_data = {
        "step": "real_data_phase1_raw_loading",
        "source_file": str(prod_path),
        "dummy_file_avoided": str(config.DUMMY_DATA_PATH),
        "is_reading_real_file": prod_path.name == "legal_knowledge_base.json",
        "total_records": total_loaded,
        "records_by_domain": domain_counts,
        "missing_field_counts": missing_fields,
        "sample_record_fields": list(sample_rec.keys()),
        "sample_record_metadata": sample_metadata,
        "raw_text_integrity": {
            "status": "PASSED" if text_integrity_passed else "FAILED",
            "matches": raw_text_matches,
            "total": total_loaded,
        },
        "status": "SUCCESS" if (total_loaded == 1237 and text_integrity_passed) else "FAILED",
    }
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
        
    print(f"Phase 1 report saved successfully to {report_path.resolve()}")
    return report_data


if __name__ == "__main__":
    validate_raw_loading()
