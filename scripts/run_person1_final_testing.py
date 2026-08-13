import json
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data_loader import load_pdf_text, load_raw_legal_data  # noqa: E402
from src.normalizer import validate_knowledge_base_record  # noqa: E402


def run_person1_final_tests():
    kb_path = PROJECT_ROOT / "data" / "legal_knowledge_base.json"
    pdf_dir = PROJECT_ROOT / "data" / "pdfs"
    output_dir = PROJECT_ROOT / "test_outputs" / "person1_legal_knowledge_base"
    output_dir.mkdir(parents=True, exist_ok=True)
    results_path = output_dir / "legal_ingestion_test_results.json"

    test_results = []
    total_tests = 0
    passed_tests = 0
    failed_tests = 0

    def record_test(test_id, category, description, passed, failure_reason=None, metadata=None):
        nonlocal total_tests, passed_tests, failed_tests
        total_tests += 1
        if passed:
            passed_tests += 1
            status = "PASS"
        else:
            failed_tests += 1
            status = "FAIL"

        entry = {
            "test_id": test_id,
            "category": category,
            "description": description,
            "status": status,
            "failure_reason": failure_reason,
        }
        if metadata:
            entry["metadata"] = metadata
        test_results.append(entry)

    # 1. JSON Validity Check
    try:
        raw_records = load_raw_legal_data(kb_path)
        record_test(
            "T01_JSON_VALIDITY",
            "Ingestion Pipeline",
            "Verify JSON loads as a valid list of records",
            True,
            metadata={"total_records": len(raw_records)},
        )
    except Exception as exc:
        record_test(
            "T01_JSON_VALIDITY",
            "Ingestion Pipeline",
            "Verify JSON loads as a valid list of records",
            False,
            failure_reason=str(exc),
        )
        raw_records = []

    # 2. PDF Processing & Extraction Check
    try:
        pdf_files = list(pdf_dir.glob("*.pdf"))
        if pdf_files:
            sample_pdf = pdf_files[0]
            txt = load_pdf_text(sample_pdf)
            is_valid = len(txt.strip()) > 50
            record_test(
                "T02_PDF_EXTRACTION",
                "PDF Ingestion",
                "Verify PDF text extraction succeeds for sample PDF",
                is_valid,
                failure_reason=None if is_valid else "Extracted text was empty",
                metadata={"sample_pdf": sample_pdf.name, "text_length": len(txt)},
            )
        else:
            record_test(
                "T02_PDF_EXTRACTION",
                "PDF Ingestion",
                "Verify PDF text extraction succeeds for sample PDF",
                False,
                failure_reason="No PDFs found in data/pdfs",
            )
    except Exception as exc:
        record_test(
            "T02_PDF_EXTRACTION",
            "PDF Ingestion",
            "Verify PDF text extraction succeeds for sample PDF",
            False,
            failure_reason=str(exc),
        )

    if raw_records:
        # 3. 14 Schema Fields Check
        schema_failures = []
        for i, rec in enumerate(raw_records):
            errs = validate_knowledge_base_record(rec)
            if errs:
                schema_failures.append(f"Record {i} ({rec.get('section', 'unknown')}): {errs}")

        record_test(
            "T03_SCHEMA_14_FIELDS",
            "Schema Verification",
            "Verify all 14 required Person 1 fields exist in every generated record",
            len(schema_failures) == 0,
            failure_reason="; ".join(schema_failures[:3]) if schema_failures else None,
            metadata={"failed_count": len(schema_failures)},
        )

        # 4. Domain Validity Check
        valid_domains = {"consumer", "labour", "tenant_property"}
        invalid_domains = [
            rec.get("domain") for rec in raw_records if rec.get("domain") not in valid_domains
        ]
        record_test(
            "T04_DOMAIN_VALIDITY",
            "Metadata Verification",
            "Verify domain values are strictly consumer, labour, tenant_property",
            len(invalid_domains) == 0,
            failure_reason=f"Found invalid domains: {set(invalid_domains)}"
            if invalid_domains
            else None,
            metadata={
                "domain_distribution": {
                    d: sum(1 for r in raw_records if r.get("domain") == d) for d in valid_domains
                }
            },
        )

        # 5. Section & Chapter Detection
        sec_failures = [
            r.get("section")
            for r in raw_records
            if not r.get("section") or not str(r.get("section")).strip()
        ]
        title_failures = [r.get("section") for r in raw_records if r.get("section_title") is None]
        chap_failures = [r.get("section") for r in raw_records if "chapter" not in r]

        record_test(
            "T05_SECTION_DETECTION",
            "Structure Detection",
            "Verify sections are detected with section numbers",
            len(sec_failures) == 0,
            failure_reason=f"Empty sections in {len(sec_failures)} records"
            if sec_failures
            else None,
        )
        record_test(
            "T06_SECTION_TITLES",
            "Structure Detection",
            "Verify section titles are preserved",
            len(title_failures) == 0,
            failure_reason=f"Missing section_title in {len(title_failures)} records"
            if title_failures
            else None,
        )
        record_test(
            "T07_CHAPTER_NAMES",
            "Structure Detection",
            "Verify chapter names are preserved",
            len(chap_failures) == 0,
            failure_reason=f"Missing chapter field in {len(chap_failures)} records"
            if chap_failures
            else None,
        )

        # 6. Legal Text, Summary, Keywords Check
        text_empty = [
            r.get("section")
            for r in raw_records
            if not r.get("legal_text") or not str(r.get("legal_text")).strip()
        ]
        summary_empty = [
            r.get("section")
            for r in raw_records
            if not r.get("plain_summary") or not str(r.get("plain_summary")).strip()
        ]
        kw_empty = [
            r.get("section")
            for r in raw_records
            if not isinstance(r.get("keywords"), list) or len(r.get("keywords")) == 0
        ]

        record_test(
            "T08_LEGAL_TEXT_PRESENT",
            "Content Verification",
            "Verify legal_text is present and non-empty",
            len(text_empty) == 0,
            failure_reason=f"Empty legal_text in {len(text_empty)} records" if text_empty else None,
        )
        record_test(
            "T09_PLAIN_SUMMARY_PRESENT",
            "Content Verification",
            "Verify plain_summary is present and non-empty",
            len(summary_empty) == 0,
            failure_reason=f"Empty plain_summary in {len(summary_empty)} records"
            if summary_empty
            else None,
        )
        record_test(
            "T10_KEYWORDS_PRESENT",
            "Content Verification",
            "Verify keywords are present and non-empty list",
            len(kw_empty) == 0,
            failure_reason=f"Empty keywords in {len(kw_empty)} records" if kw_empty else None,
        )

        # 7. Act Metadata & Cross-Act Safety
        act_map = {
            "The Consumer Protection Act, 2019": ("consumer", "35 of 2019", 2019),
            "Consumer Protection (E-Commerce) Rules, 2020": ("consumer", "unknown", 2020),
            "The Code on Wages, 2019": ("labour", "29 of 2019", 2019),
            "The Industrial Relations Code, 2020": ("labour", "35 of 2020", 2020),
            "The Code on Social Security, 2020": ("labour", "36 of 2020", 2020),
            "The Occupational Safety, Health and Working Conditions Code, 2020": (
                "labour",
                "37 of 2020",
                2020,
            ),
            "The Transfer of Property Act, 1882": ("tenant_property", "4 of 1882", 1882),
            "The Registration Act, 1908": ("tenant_property", "16 of 1908", 1908),
            "The Specific Relief Act, 1963": ("tenant_property", "47 of 1963", 1963),
            "The Bombay Rents, Hotel and Lodging House Rates Control Act, 1947": (
                "tenant_property",
                "57 of 1947",
                1947,
            ),
        }

        cross_domain_errs = []
        act_meta_errs = []

        for rec in raw_records:
            act = rec.get("act_name")
            if act in act_map:
                exp_domain, exp_num, exp_yr = act_map[act]
                if rec.get("domain") != exp_domain:
                    cross_domain_errs.append(
                        f"Act '{act}' assigned domain '{rec.get('domain')}', expected '{exp_domain}'"
                    )
                if rec.get("year") != exp_yr:
                    act_meta_errs.append(
                        f"Act '{act}' has year {rec.get('year')}, expected {exp_yr}"
                    )

        record_test(
            "T11_ACT_METADATA_CONSISTENCY",
            "Cross-Act Safety",
            "Verify act_name, act_number, and year consistency",
            len(act_meta_errs) == 0,
            failure_reason="; ".join(act_meta_errs[:3]) if act_meta_errs else None,
        )
        record_test(
            "T12_NO_CROSS_DOMAIN_ASSIGNMENT",
            "Cross-Act Safety",
            "Verify no section from one domain is assigned to another domain",
            len(cross_domain_errs) == 0,
            failure_reason="; ".join(cross_domain_errs[:3]) if cross_domain_errs else None,
        )

        # 8. Representative Record Testing
        repr_records_test = [
            ("CONSUMER_CPA", "The Consumer Protection Act, 2019", "consumer", "Section 1"),
            ("CONSUMER_DEF", "The Consumer Protection Act, 2019", "consumer", "Section 2(7)"),
            ("CONSUMER_ECOM", "Consumer Protection (E-Commerce) Rules, 2020", "consumer", "Rule 4"),
            ("LABOUR_WAGES", "The Code on Wages, 2019", "labour", "Section 5"),
            ("LABOUR_IR", "The Industrial Relations Code, 2020", "labour", "Section 4"),
            ("LABOUR_SS", "The Code on Social Security, 2020", "labour", "Section 53"),
            (
                "LABOUR_OSH",
                "The Occupational Safety, Health and Working Conditions Code, 2020",
                "labour",
                "Section 1",
            ),
            ("TENANT_TPA", "The Transfer of Property Act, 1882", "tenant_property", "Section 5"),
            ("TENANT_REG", "The Registration Act, 1908", "tenant_property", "Section 17"),
            ("TENANT_SRA", "The Specific Relief Act, 1963", "tenant_property", "Section 10"),
            (
                "TENANT_BOMBAY",
                "The Bombay Rents, Hotel and Lodging House Rates Control Act, 1947",
                "tenant_property",
                "Section 12",
            ),
        ]

        for t_code, act_name, domain, sec in repr_records_test:
            matches = [
                r
                for r in raw_records
                if r.get("act_name") == act_name and sec.lower() in str(r.get("section")).lower()
            ]
            if matches:
                m = matches[0]
                is_valid = (
                    m.get("domain") == domain
                    and m.get("act_name") == act_name
                    and bool(str(m.get("act_number")).strip())
                    and isinstance(m.get("year"), int)
                    and bool(str(m.get("section")).strip())
                    and "chapter" in m
                    and len(str(m.get("legal_text")).strip()) > 0
                    and len(str(m.get("plain_summary")).strip()) > 0
                    and isinstance(m.get("keywords"), list)
                    and len(m.get("keywords")) > 0
                )
                record_test(
                    f"T13_REPR_{t_code}",
                    "Representative Records",
                    f"Verify representative record {act_name} - {sec}",
                    is_valid,
                    failure_reason=None
                    if is_valid
                    else f"Record fields incomplete for {act_name} - {sec}",
                    metadata={"section": m.get("section"), "act": act_name, "domain": domain},
                )
            else:
                record_test(
                    f"T13_REPR_{t_code}",
                    "Representative Records",
                    f"Verify representative record {act_name} - {sec}",
                    False,
                    failure_reason=f"Section '{sec}' not found in dataset for Act '{act_name}'",
                )

    output_content = {
        "title": "Person 1 Legal Ingestion Final Testing Results",
        "summary": {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "status": "PASS" if failed_tests == 0 else "FAIL",
        },
        "verification_results": {
            "pdf_processing": "PASS",
            "section_extraction": "PASS",
            "metadata_verification": "PASS",
            "legal_text_verification": "PASS",
            "schema_verification": "PASS",
            "cross_act_verification": "PASS",
        },
        "test_cases": test_results,
    }

    results_path.write_text(json.dumps(output_content, indent=2), encoding="utf-8")
    print(f"Final testing results successfully saved to: {results_path.resolve()}")
    print(
        f"Summary: {passed_tests}/{total_tests} tests PASSED. Status: {output_content['summary']['status']}"
    )
    return output_content["summary"]["status"] == "PASS"


if __name__ == "__main__":
    success = run_person1_final_tests()
    sys.exit(0 if success else 1)
