from dataclasses import dataclass, field
from typing import Any

REQUIRED_FIELDS = {
    "id",
    "domain",
    "issue",
    "act",
    "section",
    "section_title",
    "legal_text",
}

KNOWN_OPTIONAL_FIELDS = {
    "plain_explanation",
    "applicability",
    "jurisdiction",
    "source",
    "source_url",
    "verified",
    "is_dummy",
}


@dataclass
class NormalizedLegalDocument:
    """Normalized internal representation of a legal provision or document."""

    id: str
    domain: str
    issue: str
    act: str
    section: str
    section_title: str
    legal_text: str

    # Optional fields (preserved as None if missing in source)
    plain_explanation: str | None = None
    applicability: str | None = None
    jurisdiction: str | None = None
    source: str | None = None
    source_url: str | None = None
    verified: bool | None = None
    is_dummy: bool | None = None

    # Preserved extra/unknown fields
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Converts the normalized document into a dictionary representation."""
        return {
            "id": self.id,
            "domain": self.domain,
            "issue": self.issue,
            "act": self.act,
            "section": self.section,
            "section_title": self.section_title,
            "legal_text": self.legal_text,
            "plain_explanation": self.plain_explanation,
            "applicability": self.applicability,
            "jurisdiction": self.jurisdiction,
            "source": self.source,
            "source_url": self.source_url,
            "verified": self.verified,
            "is_dummy": self.is_dummy,
            "metadata": self.metadata,
        }


def normalize_document(raw_record: dict[str, Any]) -> NormalizedLegalDocument:
    """Normalizes a single raw legal record dictionary into a NormalizedLegalDocument.

    Args:
        raw_record: Raw record dictionary from data ingestion.

    Returns:
        A NormalizedLegalDocument instance.

    Raises:
        TypeError: If raw_record is not a dictionary.
        ValueError: If any required field is missing or empty.
    """
    if not isinstance(raw_record, dict):
        raise TypeError(f"Expected raw record to be a dict, got {type(raw_record).__name__}.")

    # Check for missing or empty required fields
    missing_fields = []
    for req_field in sorted(REQUIRED_FIELDS):
        val = raw_record.get(req_field)
        if val is None or (isinstance(val, str) and not val.strip()):
            missing_fields.append(req_field)

    if missing_fields:
        doc_id_str = f" for document ID '{raw_record.get('id')}'" if raw_record.get("id") else ""
        raise ValueError(
            f"Missing or empty required field(s){doc_id_str}: {', '.join(missing_fields)}"
        )

    # Extract required fields
    doc_id = str(raw_record["id"]).strip()
    domain = str(raw_record["domain"]).strip()
    issue = str(raw_record["issue"]).strip()
    act = str(raw_record["act"]).strip()
    section = str(raw_record["section"]).strip()
    section_title = str(raw_record["section_title"]).strip()
    legal_text = str(raw_record["legal_text"]).strip()

    # Extract optional fields (preserve None if missing or None)
    plain_explanation = raw_record.get("plain_explanation")
    if plain_explanation is not None:
        plain_explanation = str(plain_explanation).strip()

    applicability = raw_record.get("applicability")
    if applicability is not None:
        applicability = str(applicability).strip()

    jurisdiction = raw_record.get("jurisdiction")
    if jurisdiction is not None:
        jurisdiction = str(jurisdiction).strip()

    source = raw_record.get("source")
    if source is not None:
        source = str(source).strip()

    source_url = raw_record.get("source_url")
    if source_url is not None:
        source_url = str(source_url).strip()

    verified = raw_record.get("verified")
    if verified is not None and not isinstance(verified, bool):
        verified = bool(verified)

    is_dummy = raw_record.get("is_dummy")
    if is_dummy is not None and not isinstance(is_dummy, bool):
        is_dummy = bool(is_dummy)

    # Capture extra unknown metadata fields
    extra_metadata: dict[str, Any] = {}

    # If raw_record has an existing 'metadata' dict, start with it
    if isinstance(raw_record.get("metadata"), dict):
        extra_metadata.update(raw_record["metadata"])

    known_keys = REQUIRED_FIELDS | KNOWN_OPTIONAL_FIELDS | {"metadata"}
    for key, value in raw_record.items():
        if key not in known_keys:
            extra_metadata[key] = value

    return NormalizedLegalDocument(
        id=doc_id,
        domain=domain,
        issue=issue,
        act=act,
        section=section,
        section_title=section_title,
        legal_text=legal_text,
        plain_explanation=plain_explanation,
        applicability=applicability,
        jurisdiction=jurisdiction,
        source=source,
        source_url=source_url,
        verified=verified,
        is_dummy=is_dummy,
        metadata=extra_metadata,
    )


def normalize_dataset(
    raw_records: list[dict[str, Any]],
) -> list[NormalizedLegalDocument]:
    """Normalizes a list of raw legal record dictionaries.

    Args:
        raw_records: List of raw dictionaries.

    Returns:
        List of NormalizedLegalDocument instances.
    """
    return [normalize_document(rec) for rec in raw_records]
