"""
document_adapter.py — Adapter between RAG Analysis Response and Phase 9 Document Engine

Maps live MultilingualProcessResponse / RAG case output into the structured legal_json
schema required by backend/document_generator.py and backend/pdf_generator.py.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from backend.document_generator import SUPPORTED_DOCUMENT_TYPES


def detect_document_type(analysis_data: Dict[str, Any], query_text: str = "") -> str:
    """
    Deterministically detect the appropriate legal notice template type
    based on retrieved statutes and factual keywords.
    """
    text_corpus = (
        query_text + " " +
        analysis_data.get("normalized_text", "") + " " +
        analysis_data.get("rights_explanation", "") + " " +
        " ".join([l.get("act", "") + " " + l.get("section", "") for l in analysis_data.get("applicable_laws", [])])
    ).lower()

    # 1. Labour / Employment notice
    if any(k in text_corpus for k in [
        "wage", "salary", "employer", "employee", "terminated", "termination",
        "gratuity", "provident fund", "stipend", "industrial relations", "bonus",
        "overtime", "unpaid wages", "code on wages", "workman"
    ]):
        return "labour_notice"

    # 2. Consumer notice
    if any(k in text_corpus for k in [
        "consumer", "defective", "defect", "product liability", "refund",
        "warranty", "goods", "service provider", "unfair trade", "ecommerce",
        "consumer protection", "damaged product", "seller"
    ]):
        return "consumer_notice"

    # 3. Tenant / Landlord notice
    if any(k in text_corpus for k in [
        "tenant", "landlord", "rent", "rental", "security deposit", "eviction",
        "lease", "premises", "rent control", "tenancy", "vacate"
    ]):
        return "tenant_notice"

    # Fallback to consumer_notice if ambiguous
    return "consumer_notice"


class LegalDocumentAdapter:
    """Adapts RAG Analysis Output to Phase 9 Legal JSON format."""

    @staticmethod
    def to_legal_json(
        analysis_data: Dict[str, Any],
        query_text: str = "",
        document_type: Optional[str] = None,
        user_info: Optional[Dict[str, str]] = None,
        opposite_party: Optional[Dict[str, str]] = None,
        amount: Optional[str] = None,
        facts: Optional[List[str]] = None,
        relief_requested: Optional[List[str]] = None,
        notice_period: Optional[str] = None,
        date_str: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Convert live RAG response dictionary into Phase 9 structured legal JSON.
        """
        # Determine document type
        if document_type and document_type in SUPPORTED_DOCUMENT_TYPES:
            final_doc_type = document_type
        else:
            final_doc_type = detect_document_type(analysis_data, query_text)

        # Build user info
        user = user_info or {}
        sender_name = user.get("name", "[Sender Name / Aggrieved Party]")
        sender_address = user.get("address", "[Sender Address, City, State]")

        # Build opposite party info
        party = opposite_party or {}
        recipient_name = party.get("name", "[Opposite Party / Respondent Name]")
        recipient_address = party.get("address", "[Recipient Office Address, City, State]")

        # Build issue info
        raw_query = query_text or analysis_data.get("normalized_text", "Legal Dispute")
        issue_title = raw_query.rstrip(".").capitalize()
        if len(issue_title) > 80:
            issue_title = issue_title[:77] + "..."

        issue_desc = analysis_data.get("normalized_text") or raw_query

        # Facts
        if facts and len(facts) > 0:
            final_facts = facts
        else:
            final_facts = [
                f"The Complainant / Claimant states that: {issue_desc}",
                "The Complainant has repeatedly requested amicable resolution, which has not been fulfilled by the Addressee."
            ]

        # Rights
        rights_text = analysis_data.get("rights_explanation", "")
        if rights_text and "could not find sufficiently relevant" not in rights_text.lower():
            sentences = [s.strip() for s in rights_text.replace("\n", ". ").split(". ") if len(s.strip()) > 15]
            final_rights = sentences[:4] if sentences else [rights_text[:200]]
        else:
            final_rights = [
                "The Complainant is legally entitled to full protection and remedies provided under applicable laws of India."
            ]

        # Laws
        raw_laws = analysis_data.get("applicable_laws", [])
        final_laws = []
        for l in raw_laws:
            if isinstance(l, dict):
                act_str = l.get("act", "Statutory Provision")
                sec_str = l.get("section", "Section")
                expl_str = l.get("explanation", "")
            else:
                act_str = getattr(l, "act", "Statutory Provision")
                sec_str = getattr(l, "section", "Section")
                expl_str = getattr(l, "explanation", "")

            final_laws.append({
                "act": act_str,
                "section": sec_str,
                "title": sec_str,
                "explanation": expl_str
            })

        # Recommended Actions
        actions = analysis_data.get("recommended_actions", [])
        if not actions or len(actions) == 0:
            actions = [
                "Preserve all relevant records, notices, communications, and proofs.",
                "Comply with the demands raised in this notice within the stipulated timeline."
            ]

        # Relief Requested
        if relief_requested and len(relief_requested) > 0:
            final_relief = relief_requested
        else:
            if final_doc_type == "labour_notice":
                final_relief = [
                    "Immediate release and disbursement of all outstanding salary and dues.",
                    "Issuance of experience certificate and formal statement of account."
                ]
            elif final_doc_type == "consumer_notice":
                final_relief = [
                    "Full refund or replacement of the defective product/service.",
                    "Payment of adequate compensation for harassment, mental agony, and financial loss."
                ]
            elif final_doc_type == "tenant_notice":
                final_relief = [
                    "Full refund and return of the security deposit amount.",
                    "Cessation of any illegal eviction or interference with lawful possession."
                ]
            else:
                final_relief = ["Redressal of grievance and compliance with statutory obligations."]

        # Sources
        sources = [l.get("source") for l in final_laws if l.get("source")]

        # Date
        today_str = date_str or datetime.today().strftime("%d %B %Y")

        return {
            "document_type": final_doc_type,
            "user": {
                "name": sender_name,
                "address": sender_address
            },
            "opposite_party": {
                "name": recipient_name,
                "address": recipient_address
            },
            "issue": {
                "title": issue_title,
                "description": issue_desc,
                "amount": amount or ""
            },
            "facts": final_facts,
            "rights": final_rights,
            "laws": final_laws,
            "recommended_actions": actions,
            "relief_requested": final_relief,
            "sources": sources,
            "date": today_str,
            "notice_period": notice_period or "15 days"
        }
