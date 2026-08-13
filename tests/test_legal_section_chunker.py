from src.legal_section_chunker import (
    chunk_legal_pdf_text,
    clean_legal_text,
    extract_keywords,
    generate_plain_summary,
)


def test_clean_legal_text():
    """Test cleaning gazette headers/footers and fixing whitespace."""
    raw = "THE GAZETTE OF INDIA EXTRAORDINARY [P ART II—SEC. 1]\n\nSome legal text.\ufffd\n\n\n\nMore text."
    cleaned = clean_legal_text(raw)
    assert "GAZETTE OF INDIA" not in cleaned
    assert "\ufffd" not in cleaned
    assert "Some legal text." in cleaned
    assert "More text." in cleaned


def test_clean_legal_text_empty():
    """Test clean_legal_text with empty or None input."""
    assert clean_legal_text("") == ""


def test_extract_keywords():
    """Test keyword extraction for consumer legal text."""
    sec = "Section 2(7)"
    sec_title = "Consumer Definition"
    text = "Consumer means any person who buys goods or hires services."
    keywords = extract_keywords(sec, sec_title, text)
    assert isinstance(keywords, list)
    assert "consumer" in keywords
    assert "goods" in keywords
    assert "services" in keywords


def test_generate_plain_summary():
    """Test plain summary generation for specific sections."""
    summary_2_7 = generate_plain_summary("Section 2(7)", "Consumer", "Full text")
    assert "Defines a consumer" in summary_2_7

    summary_defect = generate_plain_summary("Section 2(10)", "Defect", "Full text")
    assert "Defines a defect" in summary_defect

    summary_general = generate_plain_summary(
        "Section 15", "Appeals", "General text for appeal procedures."
    )
    assert "This section establishes legal rules regarding 'Appeals'" in summary_general


def test_chunk_legal_pdf_text_sample():
    """Test chunking mock legal text into section records."""
    sample_text = """
    THE CONSUMER PROTECTION ACT, 2019
    NO. 35 OF 2019

    CHAPTER I
    Preliminary

    1. (1) This Act may be called the Consumer Protection Act, 2019.
    (2) It extends to the whole of India.

    2. In this Act, unless the context otherwise requires,--
    (1) "advertisement" means any audio or visual publicity;
    (7) "consumer" means any person who buys any goods;

    CHAPTER II
    Consumer Protection Councils

    3. (1) The Central Government shall, by notification, establish...
    """

    records = chunk_legal_pdf_text(sample_text)
    assert len(records) >= 2

    sec1_record = next((r for r in records if r["section"] == "Section 1"), None)
    assert sec1_record is not None
    assert sec1_record["domain"] == "consumer"
    assert sec1_record["act_name"] == "Consumer Protection Act, 2019"
    assert sec1_record["act_number"] == "35 of 2019"
    assert sec1_record["year"] == 2019
    assert sec1_record["chapter"] == "Preliminary"

    sec2_record = next((r for r in records if r["section"] == "Section 2(7)"), None)
    assert sec2_record is not None
    assert sec2_record["section_title"] == "Consumer"
    assert sec2_record["verified"] is True
