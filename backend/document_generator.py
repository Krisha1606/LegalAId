"""
document_generator.py — LegalAId Phase 9: Legal Document Template Engine

Accepts structured legal JSON and produces editable document fields.

Flow:
    RAG System / Dummy Data
            ↓
    Structured Legal JSON
            ↓
    document_generator.generate()
            ↓
    Editable Document Fields
            ↓
    Frontend Editor / PDF Generator

Supported document types:
    - labour_notice
    - consumer_notice
    - tenant_notice
"""

from typing import Any


SUPPORTED_DOCUMENT_TYPES = {
    "labour_notice",
    "consumer_notice",
    "tenant_notice",
}


def _list_value(value: Any) -> list:
    """Safely convert a value into a list."""
    if value is None:
        return []

    if isinstance(value, list):
        return value

    return [value]


def _get_common_fields(data: dict) -> tuple:
    """Extract common user, opposite-party and issue information."""
    user = data.get("user") or {}
    party = data.get("opposite_party") or {}
    issue = data.get("issue") or {}

    if not isinstance(user, dict):
        user = {}

    if not isinstance(party, dict):
        party = {}

    if not isinstance(issue, dict):
        issue = {}

    return user, party, issue


def _notice_period(data: dict) -> str:
    """
    Get the notice period from structured legal data.

    This avoids hardcoding a legal deadline such as 15 days.
    """
    period = data.get("notice_period", "")

    if period is None:
        return ""

    return str(period).strip()


def _common_fields(data: dict) -> dict:
    """Build fields shared by all document types."""
    user, party, issue = _get_common_fields(data)

    return {
        "sender_name": user.get("name", ""),
        "sender_address": user.get("address", ""),
        "recipient_name": party.get("name", ""),
        "recipient_address": party.get("address", ""),
        "date": data.get("date", ""),
        "amount": issue.get("amount", ""),
        "issue_description": issue.get("description", ""),
        "facts": _list_value(data.get("facts")),
        "rights": _list_value(data.get("rights")),
        "laws": _list_value(data.get("laws")),
        "recommended_actions": _list_value(
            data.get("recommended_actions")
        ),
        "relief_requested": _list_value(
            data.get("relief_requested")
        ),
        "sources": _list_value(data.get("sources")),
        "notice_period": _notice_period(data),
    }


def generate(legal_json: dict) -> dict:
    """
    Main entry point.

    Args:
        legal_json: Structured legal JSON from dummy data
                   or the future RAG system.

    Returns:
        Editable document fields.

    Raises:
        ValueError: If input is invalid or document type is unsupported.
    """

    if not isinstance(legal_json, dict):
        raise ValueError("legal_json must be a JSON object.")

    doc_type = legal_json.get("document_type")

    if not doc_type:
        raise ValueError(
            "Missing required field: 'document_type'."
        )

    if doc_type not in SUPPORTED_DOCUMENT_TYPES:
        raise ValueError(
            f"Unsupported document_type: '{doc_type}'. "
            f"Supported types: {', '.join(sorted(SUPPORTED_DOCUMENT_TYPES))}"
        )

    if doc_type == "labour_notice":
        return _labour_notice(legal_json)

    if doc_type == "consumer_notice":
        return _consumer_notice(legal_json)

    if doc_type == "tenant_notice":
        return _tenant_notice(legal_json)

    raise ValueError(
        f"Unsupported document_type: '{doc_type}'."
    )


# ---------------------------------------------------------------------------
# Labour Notice
# ---------------------------------------------------------------------------

def _labour_notice(data: dict) -> dict:
    user, party, issue = _get_common_fields(data)
    fields = _common_fields(data)

    user_name = user.get("name", "[Name]")
    user_address = user.get("address", "[Address]")
    party_name = party.get("name", "[Recipient]")
    party_address = party.get("address", "[Recipient Address]")
    issue_title = issue.get("title", "Employment Dispute")

    period = fields["notice_period"]

    closing = (
        "You are hereby called upon to comply with the above relief"
    )

    if period:
        closing += (
            f" within {period} of the receipt of this notice"
        )

    closing += (
        ", failing which I shall be constrained to initiate "
        "appropriate legal proceedings against you at your risk and cost."
    )

    return {
        "document_type": "labour_notice",
        "template_title": "Legal Notice — Labour / Employment Matter",

        **fields,

        "subject": (
            f"Legal Notice — {issue_title}"
        ),

        "opening": (
            f"I, {user_name}, residing at {user_address}, "
            f"am issuing this legal notice to {party_name}, "
            f"having its office at {party_address}, "
            f"regarding {issue_title}."
        ),

        "closing": closing,
    }


# ---------------------------------------------------------------------------
# Consumer Notice
# ---------------------------------------------------------------------------

def _consumer_notice(data: dict) -> dict:
    user, party, issue = _get_common_fields(data)
    fields = _common_fields(data)

    user_name = user.get("name", "[Name]")
    user_address = user.get("address", "[Address]")
    party_name = party.get("name", "[Recipient]")
    party_address = party.get("address", "[Recipient Address]")
    issue_title = issue.get("title", "Consumer Dispute")

    period = fields["notice_period"]

    closing = (
        "You are hereby directed to redress the above grievance "
        "and provide the relief sought"
    )

    if period:
        closing += f" within {period} of receipt of this notice"

    closing += (
        ", failing which I shall be constrained to file a formal "
        "complaint before the appropriate Consumer Forum / Commission "
        "at your risk and cost."
    )

    return {
        "document_type": "consumer_notice",
        "template_title": "Legal Notice — Consumer Complaint",

        **fields,

        "subject": (
            f"Consumer Complaint Notice — {issue_title}"
        ),

        "opening": (
            f"I, {user_name}, residing at {user_address}, "
            f"am issuing this consumer complaint notice to {party_name}, "
            f"having its registered office at {party_address}, "
            f"regarding {issue_title}."
        ),

        "closing": closing,
    }


# ---------------------------------------------------------------------------
# Tenant / Rental Notice
# ---------------------------------------------------------------------------

def _tenant_notice(data: dict) -> dict:
    user, party, issue = _get_common_fields(data)
    fields = _common_fields(data)

    user_name = user.get("name", "[Name]")
    user_address = user.get("address", "[Address]")
    party_name = party.get("name", "[Recipient]")
    party_address = party.get("address", "[Recipient Address]")
    issue_title = issue.get("title", "Tenant / Rental Dispute")

    period = fields["notice_period"]

    closing = (
        "You are hereby called upon to comply with the above demands"
    )

    if period:
        closing += f" within {period} of receipt of this notice"

    closing += (
        ", failing which I shall be constrained to initiate "
        "appropriate legal proceedings before the competent authority "
        "at your risk and cost."
    )

    return {
        "document_type": "tenant_notice",
        "template_title": "Legal Notice — Tenant / Rental Dispute",

        **fields,

        "subject": (
            f"Legal Notice — {issue_title}"
        ),

        "opening": (
            f"I, {user_name}, residing at {user_address}, "
            f"am issuing this legal notice to {party_name}, "
            f"residing/having office at {party_address}, "
            f"regarding {issue_title}."
        ),

        "closing": closing,
    }