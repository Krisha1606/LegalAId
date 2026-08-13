import re
from dataclasses import dataclass, field
from typing import Any

from src.normalizer import NormalizedLegalDocument


@dataclass
class Chunk:
    """Retrieval-ready legal text chunk with complete source & citation traceability."""

    chunk_id: str
    document_id: str
    parent_document_id: str
    chunk_index: int
    total_chunks: int
    text: str

    domain: str
    issue: str
    act: str
    section: str
    section_title: str

    plain_explanation: str | None = None
    applicability: str | None = None
    jurisdiction: str | None = None
    source: str | None = None
    source_url: str | None = None
    verified: bool | None = None
    is_dummy: bool | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Converts chunk instance to dictionary representation."""
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "parent_document_id": self.parent_document_id,
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks,
            "text": self.text,
            "domain": self.domain,
            "issue": self.issue,
            "act": self.act,
            "section": self.section,
            "section_title": self.section_title,
            "plain_explanation": self.plain_explanation,
            "applicability": self.applicability,
            "jurisdiction": self.jurisdiction,
            "source": self.source,
            "source_url": self.source_url,
            "verified": self.verified,
            "is_dummy": self.is_dummy,
            "metadata": self.metadata,
        }


def _split_text_legally(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Splits text into chunks prioritizing legal boundaries (paragraphs, sentences)
    and applying controlled overlap when splitting.

    Args:
        text: Raw text to split.
        chunk_size: Maximum character length per chunk.
        chunk_overlap: Overlap character count when splitting.

    Returns:
        List of text segment strings.
    """
    text = text.strip()
    if not text:
        return []

    if len(text) <= chunk_size:
        return [text]

    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

    atomic_units: list[str] = []
    for para in paragraphs:
        if len(para) <= chunk_size:
            atomic_units.append(para)
        else:
            sentences = [s.strip() for s in re.split(r"(?<=[.;:])\s+", para) if s.strip()]
            for sentence in sentences:
                if len(sentence) <= chunk_size:
                    atomic_units.append(sentence)
                else:
                    words = sentence.split()
                    for w in words:
                        atomic_units.append(w)

    chunks: list[str] = []
    current_words: list[str] = []
    current_len = 0

    for unit in atomic_units:
        unit_words = unit.split()
        for word in unit_words:
            word_len = len(word)
            added_len = word_len + (1 if current_words else 0)

            if current_words and (current_len + added_len > chunk_size):
                chunk_str = " ".join(current_words).strip()
                chunks.append(chunk_str)

                overlap_words: list[str] = []
                overlap_char_cnt = 0
                for w in reversed(current_words):
                    w_len = len(w) + (1 if overlap_words else 0)
                    if overlap_char_cnt + w_len <= chunk_overlap or not overlap_words:
                        overlap_words.insert(0, w)
                        overlap_char_cnt += w_len
                    else:
                        break

                current_words = overlap_words
                current_len = sum(len(w) for w in current_words) + max(0, len(current_words) - 1)

            current_words.append(word)
            current_len += word_len + (1 if len(current_words) > 1 else 0)

    if current_words:
        final_chunk = " ".join(current_words).strip()
        if not chunks or final_chunk != chunks[-1]:
            chunks.append(final_chunk)

    return chunks if chunks else [text]


def chunk_document(
    doc: NormalizedLegalDocument,
    chunk_size: int = 500,
    chunk_overlap: int = 100,
) -> list[Chunk]:
    """Chunks a normalized legal document while preserving full traceability & metadata.

    Args:
        doc: NormalizedLegalDocument instance.
        chunk_size: Maximum character count per chunk.
        chunk_overlap: Character overlap when splitting long provisions.

    Returns:
        List of Chunk objects.

    Raises:
        ValueError: If chunk_size <= 0 or chunk_overlap < 0 or chunk_overlap >= chunk_size.
    """
    if chunk_size <= 0:
        raise ValueError(f"chunk_size must be positive, got {chunk_size}")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError(
            f"chunk_overlap must be non-negative and less than chunk_size ({chunk_size}), got {chunk_overlap}"
        )

    text_segments = _split_text_legally(doc.legal_text, chunk_size, chunk_overlap)
    if not text_segments:
        return []

    total_chunks = len(text_segments)
    chunks: list[Chunk] = []

    for idx, seg in enumerate(text_segments):
        chunk_id = f"{doc.id}-chunk-{idx}"
        chunk_obj = Chunk(
            chunk_id=chunk_id,
            document_id=doc.id,
            parent_document_id=doc.id,
            chunk_index=idx,
            total_chunks=total_chunks,
            text=seg,
            domain=doc.domain,
            issue=doc.issue,
            act=doc.act,
            section=doc.section,
            section_title=doc.section_title,
            plain_explanation=doc.plain_explanation,
            applicability=doc.applicability,
            jurisdiction=doc.jurisdiction,
            source=doc.source,
            source_url=doc.source_url,
            verified=doc.verified,
            is_dummy=doc.is_dummy,
            metadata=dict(doc.metadata),
        )
        chunks.append(chunk_obj)

    return chunks


def chunk_dataset(
    docs: list[NormalizedLegalDocument],
    chunk_size: int = 500,
    chunk_overlap: int = 100,
) -> list[Chunk]:
    """Chunks a list of normalized legal documents.

    Args:
        docs: List of NormalizedLegalDocument instances.
        chunk_size: Maximum character count per chunk.
        chunk_overlap: Character overlap when splitting long provisions.

    Returns:
        List of all Chunk objects across the dataset.
    """
    all_chunks: list[Chunk] = []
    for doc in docs:
        all_chunks.extend(chunk_document(doc, chunk_size=chunk_size, chunk_overlap=chunk_overlap))
    return all_chunks
