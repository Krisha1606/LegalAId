"""Module for parsing official legal PDF Acts into section and chapter level records."""

import re
from typing import Any

COMMON_CONSUMER_KEYWORDS = {
    "consumer",
    "goods",
    "services",
    "purchase",
    "buyer",
    "seller",
    "complaint",
    "dispute",
    "compensation",
    "defect",
    "deficiency",
    "refund",
    "replacement",
    "e-commerce",
    "liability",
    "product",
    "advertisement",
    "misleading",
    "authority",
    "commission",
    "council",
    "district",
    "state",
    "national",
    "mediation",
    "penalty",
    "offence",
}


def clean_legal_text(text: str) -> str:
    """Cleans official legal text by stripping gazette page artifacts and fixing character encodings."""
    if not text:
        return ""

    # Remove gazette publication headers and footers
    text = re.sub(r"THE GAZETTE OF INDIA EXTRAORDINARY\s+\[P\s*ART II—[^\n]*\]", "", text)
    text = re.sub(r"SEC\.\s*1\]\s+THE GAZETTE OF INDIA EXTRAORDINARY\s+\d*", "", text)
    text = re.sub(r"REGISTERED NO\.[^\n]+", "", text)
    text = re.sub(r"jftLV[^\n]+", "", text)
    text = re.sub(r"bl Hkkx[^\n]+", "", text)
    text = re.sub(r"vlk/kkj.k[^\n]+", "", text)
    text = re.sub(r"Hkkx  II[^\n]+", "", text)
    text = re.sub(r"izkf/kdkj[^\n]+", "", text)
    text = re.sub(r"la[^\n]+", "", text)
    text = re.sub(r"No\.\s*\d+\][^\n]+", "", text)
    text = re.sub(r"Separate paging[^\n]+", "", text)

    # Fix character artifacts from PDF font encoding
    text = text.replace("\ufffd", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_keywords(section: str, section_title: str, legal_text: str) -> list[str]:
    """Extracts search keywords for a legal provision."""
    combined = f"{section} {section_title} {legal_text}".lower()
    words = re.findall(r"[a-z]{3,}", combined)

    found = set()
    for w in words:
        if w in COMMON_CONSUMER_KEYWORDS:
            found.add(w)

    if not found:
        found = {"consumer", "legal", "provision", "section"}

    # Include title terms
    title_words = [w.lower() for w in re.findall(r"[a-z]{3,}", section_title)]
    for tw in title_words[:3]:
        if len(tw) > 3:
            found.add(tw)

    return sorted(list(found))


def generate_plain_summary(section: str, section_title: str, legal_text: str) -> str:
    """Generates a plain-language explanation of a legal section."""
    sec_lower = section.lower()
    title_lower = section_title.lower()

    if "2(7)" in sec_lower or title_lower == "consumer":
        return (
            "Defines a consumer as any individual who buys goods or hires services for personal use "
            "or livelihood through offline or online means, excluding purchases for commercial resale."
        )
    if "2(1)" in sec_lower or title_lower == "advertisement":
        return "Defines advertisements to include audio, visual, or written endorsements promoting goods or services."
    if "2(10)" in sec_lower or title_lower == "defect":
        return "Defines a defect as any fault, imperfection, or shortcoming in quality, quantity, or purity of goods."
    if "2(11)" in sec_lower or title_lower == "deficiency":
        return "Defines deficiency of service as any fault, imperfection, or inadequacy in performance quality or standard."
    if "2(14)" in sec_lower or title_lower == "e-commerce":
        return "Defines e-commerce as buying or selling of goods or services including digital products over digital or electronic networks."
    if "2(43)" in sec_lower or "2(45)" in sec_lower or "unfair trade practice" in title_lower:
        return "Defines unfair trade practices including misleading advertisements, false quality claims, or deceptive pricing."
    if "short title" in title_lower or section == "Section 1":
        return "Specifies the official name of the Act, its nationwide territorial coverage, and its application to all goods and services."

    # General descriptive plain summary generator based on section title
    clean_text_first = legal_text.replace("\n", " ").strip()
    if len(clean_text_first) > 200:
        clean_text_first = clean_text_first[:200] + "..."

    return f"This section establishes legal rules regarding '{section_title.strip()}'. Summary provision: {clean_text_first}"


def chunk_legal_pdf_text(
    full_text: str,
    domain: str = "consumer",
    source_name: str = "India Code",
    source_url: str = "https://www.indiacode.nic.in/handle/123456789/15256",
    last_verified: str = "2026-08-13",
) -> list[dict[str, Any]]:
    """Chunks full official PDF text into section/chapter legal records.

    Args:
        full_text: Extracted raw text from legal PDF.
        domain: Legal domain name (default: "consumer").
        source_name: Official source name (default: "India Code").
        source_url: Official source URL.
        last_verified: Verification date string.

    Returns:
        List of JSON records matching Person 1 schema.
    """
    clean_text = clean_legal_text(full_text)

    # Act Name, Number, Year
    act_name = "Consumer Protection Act, 2019"
    act_number = "35 of 2019"
    year = 2019

    name_match = re.search(
        r"THE\s+(CONSUMER\s+PROTECTION\s+ACT,\s*2019)", clean_text, re.IGNORECASE
    )
    if name_match:
        act_name = "Consumer Protection Act, 2019"

    num_match = re.search(r"NO\.\s*(\d+\s+OF\s+\d{4})", clean_text, re.IGNORECASE)
    if num_match:
        num_str = num_match.group(1).lower().replace("of", "of")
        parts = num_str.split("of")
        if len(parts) == 2:
            act_number = f"{parts[0].strip()} of {parts[1].strip()}"
            year = int(parts[1].strip())

    # Detect Chapters
    chapter_matches = list(re.finditer(r"CHAPTER\s+([IVXLCDM]+)\s*\n+\s*([^\n]+)", clean_text))
    chapters = []
    for m in chapter_matches:
        num = m.group(1)
        name = m.group(2).strip()
        name = re.sub(r"^[A-Z]\s+", "", name)
        chapters.append((m.start(), name.title()))

    def get_chapter(pos: int) -> str:
        current = "Preliminary"
        for ch_pos, ch_name in chapters:
            if pos >= ch_pos:
                current = ch_name
            else:
                break
        return current

    records: list[dict[str, Any]] = []

    # 1. Section 1
    sec1_match = re.search(r"1\.\s+\(1\)[\s\S]*?(?=\n\s*2\.\s+In this Act)", clean_text)
    if sec1_match:
        txt = sec1_match.group(0).strip()
        rec = {
            "domain": domain,
            "act_name": act_name,
            "act_number": act_number,
            "year": year,
            "section": "Section 1",
            "section_title": "Short title, extent, commencement and application",
            "chapter": "Preliminary",
            "legal_text": txt,
            "plain_summary": generate_plain_summary(
                "Section 1", "Short title, extent, commencement and application", txt
            ),
            "keywords": extract_keywords(
                "Section 1", "Short title, extent, commencement and application", txt
            ),
            "source_name": source_name,
            "source_url": source_url,
            "verified": True,
            "last_verified": last_verified,
        }
        records.append(rec)

    # 2. Section 2 Subsections (Definitions)
    sec2_match = re.search(
        r"2\.\s+In this Act, unless the context otherwise requires,[\s\S]*?(?=\n\s*CHAPTER II|\n\s*3\.\s+)",
        clean_text,
    )
    if sec2_match:
        sec2_text = sec2_match.group(0)
        sub_pattern = re.compile(r"\n\s*\(\s*(\d+)\s*\)\s*\"([^\"]+)\"\s*", re.IGNORECASE)
        sub_matches = list(sub_pattern.finditer(sec2_text))

        for i, sub in enumerate(sub_matches):
            num = sub.group(1)
            term = sub.group(2).strip()
            start = sub.start()
            end = sub_matches[i + 1].start() if i + 1 < len(sub_matches) else len(sec2_text)
            body = sec2_text[start:end].strip()

            sec_str = f"Section 2({num})"
            title_str = term.strip().title()

            rec = {
                "domain": domain,
                "act_name": act_name,
                "act_number": act_number,
                "year": year,
                "section": sec_str,
                "section_title": title_str,
                "chapter": "Preliminary",
                "legal_text": body,
                "plain_summary": generate_plain_summary(sec_str, title_str, body),
                "keywords": extract_keywords(sec_str, title_str, body),
                "source_name": source_name,
                "source_url": source_url,
                "verified": True,
                "last_verified": last_verified,
            }
            records.append(rec)

    # 3. Main Sections 3 to 107
    sec_pattern = re.compile(r"\n\s*(\d+)\.\s+", re.MULTILINE)
    sec_matches = list(sec_pattern.finditer(clean_text))

    for i, m in enumerate(sec_matches):
        sec_num_str = m.group(1)
        sec_num = int(sec_num_str)
        if sec_num <= 2:
            continue

        start = m.start()
        end = sec_matches[i + 1].start() if i + 1 < len(sec_matches) else len(clean_text)
        sec_block = clean_text[start:end].strip()

        ch_name = get_chapter(start)

        # Detect margin title if present before section start
        prev_snippet = clean_text[max(0, start - 120) : start]
        lines = [line.strip() for line in prev_snippet.split("\n") if line.strip()]
        title_str = f"Provision of Section {sec_num}"
        if lines:
            possible = lines[-1]
            if len(possible) > 3 and not possible.startswith("CHAPTER"):
                title_str = possible.rstrip(".")

        sec_str = f"Section {sec_num}"
        rec = {
            "domain": domain,
            "act_name": act_name,
            "act_number": act_number,
            "year": year,
            "section": sec_str,
            "section_title": title_str,
            "chapter": ch_name,
            "legal_text": sec_block,
            "plain_summary": generate_plain_summary(sec_str, title_str, sec_block),
            "keywords": extract_keywords(sec_str, title_str, sec_block),
            "source_name": source_name,
            "source_url": source_url,
            "verified": True,
            "last_verified": last_verified,
        }
        records.append(rec)

    return records
