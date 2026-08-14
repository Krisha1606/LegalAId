from dataclasses import dataclass, field
from typing import Any

from src.config import config
from src.embedder import LegalEmbedder
from src.vector_store import FAISSVectorStore


@dataclass
class RetrievedLegalChunk:
    """Represents a single retrieved legal chunk with FAISS similarity score and complete metadata."""

    rank: int
    score: float
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
    is_qualified: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Converts retrieved legal chunk into dictionary representation."""
        return {
            "rank": self.rank,
            "score": round(float(self.score), 4),
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
            "is_qualified": self.is_qualified,
        }


@dataclass
class RetrievalResult:
    """Represents full semantic retrieval response for a user query."""

    query: str
    top_k: int
    similarity_threshold: float
    candidates: list[RetrievedLegalChunk]
    qualified_chunks: list[RetrievedLegalChunk]
    status: str

    def to_dict(self) -> dict[str, Any]:
        """Converts retrieval result to serialized dictionary representation."""
        return {
            "query": self.query,
            "top_k": self.top_k,
            "similarity_threshold": self.similarity_threshold,
            "status": self.status,
            "candidates_count": len(self.candidates),
            "qualified_count": len(self.qualified_chunks),
            "candidates": [c.to_dict() for c in self.candidates],
            "qualified_chunks": [c.to_dict() for c in self.qualified_chunks],
        }


class LegalRetriever:
    """Modular Semantic Legal Retriever executing vector search, metadata recovery, and threshold filtering."""

    def __init__(
        self,
        embedder: LegalEmbedder | None = None,
        vector_store: FAISSVectorStore | None = None,
        top_k: int | None = None,
        similarity_threshold: float | None = None,
    ) -> None:
        """Initializes LegalRetriever.

        Args:
            embedder: LegalEmbedder instance. Defaults to new instance with config.EMBEDDING_MODEL.
            vector_store: FAISSVectorStore instance. Defaults to loading from config.VECTOR_STORE_PATH.
            top_k: Default Top-K count. Defaults to config.TOP_K (5).
            similarity_threshold: Default score threshold. Defaults to config.SIMILARITY_THRESHOLD (0.35).
        """
        self.embedder = embedder or LegalEmbedder()
        self.vector_store = vector_store or FAISSVectorStore()

        if self.vector_store.ntotal == 0 and self.vector_store.dir_path.exists():
            try:
                self.vector_store.load()
            except FileNotFoundError:
                pass

        self.default_top_k = top_k if top_k is not None else config.TOP_K
        self.default_threshold = (
            similarity_threshold
            if similarity_threshold is not None
            else config.SIMILARITY_THRESHOLD
        )

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        similarity_threshold: float | None = None,
    ) -> RetrievalResult:
        """Performs semantic vector search for a user query and returns ranked & qualified legal chunks.

        Args:
            query: User search query string.
            top_k: Override Top-K count.
            similarity_threshold: Override similarity threshold.

        Returns:
            RetrievalResult object.

        Raises:
            ValueError: If query is empty or invalid, or top_k <= 0.
        """
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Retrieval query must be a non-empty string.")

        target_k = top_k if top_k is not None else self.default_top_k
        if target_k <= 0:
            raise ValueError(f"top_k must be positive, got {target_k}")

        threshold = (
            similarity_threshold if similarity_threshold is not None else self.default_threshold
        )

        if self.vector_store.ntotal == 0:
            return RetrievalResult(
                query=query.strip(),
                top_k=target_k,
                similarity_threshold=threshold,
                candidates=[],
                qualified_chunks=[],
                status="insufficient_retrieval",
            )

        effective_k = min(target_k, self.vector_store.ntotal)

        # 1. Embed user query using LegalEmbedder
        query_vector = self.embedder.embed_query(query.strip())

        # 2. Search FAISS index
        distances, indices = self.vector_store.search_raw_vector(query_vector, top_k=effective_k)

        candidates: list[RetrievedLegalChunk] = []
        raw_distances = distances[0]
        raw_indices = indices[0]

        for i in range(len(raw_indices)):
            pos = int(raw_indices[i])
            if pos < 0:
                continue
            score = float(raw_distances[i])
            meta = self.vector_store.get_chunk_by_position(pos)

            is_qual = score >= threshold

            chunk_obj = RetrievedLegalChunk(
                rank=i + 1,
                score=score,
                chunk_id=meta.get("chunk_id", ""),
                document_id=meta.get("document_id", ""),
                parent_document_id=meta.get("parent_document_id", ""),
                chunk_index=meta.get("chunk_index", 0),
                total_chunks=meta.get("total_chunks", 1),
                text=meta.get("text", ""),
                domain=meta.get("domain", ""),
                issue=meta.get("issue", ""),
                act=meta.get("act", ""),
                section=meta.get("section", ""),
                section_title=meta.get("section_title", ""),
                plain_explanation=meta.get("plain_explanation"),
                applicability=meta.get("applicability"),
                jurisdiction=meta.get("jurisdiction"),
                source=meta.get("source"),
                source_url=meta.get("source_url"),
                verified=meta.get("verified"),
                is_dummy=meta.get("is_dummy"),
                metadata=meta.get("metadata", {}),
                is_qualified=is_qual,
            )
            candidates.append(chunk_obj)

        # Sort candidates by score descending
        candidates.sort(key=lambda c: c.score, reverse=True)
        for idx, c in enumerate(candidates):
            c.rank = idx + 1

        qualified_chunks = [c for c in candidates if c.is_qualified]
        status = "success" if len(qualified_chunks) > 0 else "insufficient_retrieval"

        return RetrievalResult(
            query=query.strip(),
            top_k=target_k,
            similarity_threshold=threshold,
            candidates=candidates,
            qualified_chunks=qualified_chunks,
            status=status,
        )
