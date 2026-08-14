import os
import time
import logging
from dataclasses import dataclass, field
from typing import Any, List, Optional

from sentence_transformers import CrossEncoder

from src.config import config
from src.retriever import LegalRetriever, RetrievalResult, RetrievedLegalChunk

logger = logging.getLogger(__name__)


@dataclass
class RerankedChunk(RetrievedLegalChunk):
    """Retrieved legal chunk enhanced with second-stage Cross-Encoder reranking scores and relevance classification."""

    rerank_score: float = 0.0
    relevance_decision: str = "irrelevant"  # "directly_relevant", "related_but_insufficient", "irrelevant"

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["rerank_score"] = round(float(self.rerank_score), 4)
        d["relevance_decision"] = self.relevance_decision
        return d


class LegalReranker:
    """Modular Second-Stage Cross-Encoder Reranker & Relevance Validator.

    Performs candidate reranking after FAISS vector retrieval and validates legal relevance
    before passing context to Ollama LLM.
    """

    def __init__(
        self,
        retriever: Optional[LegalRetriever] = None,
        model_name: Optional[str] = None,
        top_n: Optional[int] = None,
        rerank_threshold: Optional[float] = None,
        top_k: Optional[int] = None,
    ) -> None:
        """Initializes LegalReranker with first-stage retriever and local Cross-Encoder model."""
        self.retriever = retriever or LegalRetriever()
        self.model_name = model_name or config.RERANKER_MODEL
        self.top_n = top_n if top_n is not None else config.RERANK_TOP_N
        self.rerank_threshold = (
            rerank_threshold if rerank_threshold is not None else config.RERANK_SCORE_THRESHOLD
        )
        self.top_k = top_k if top_k is not None else config.TOP_K

        logger.info(f"Loading Cross-Encoder model: {self.model_name}")
        old_offline_hub = os.environ.pop("HF_HUB_OFFLINE", None)
        old_offline_tr = os.environ.pop("TRANSFORMERS_OFFLINE", None)
        try:
            self.cross_encoder = CrossEncoder(self.model_name)
        finally:
            if old_offline_hub is not None:
                os.environ["HF_HUB_OFFLINE"] = old_offline_hub
            if old_offline_tr is not None:
                os.environ["TRANSFORMERS_OFFLINE"] = old_offline_tr

    def rerank(
        self,
        query: str,
        top_n: Optional[int] = None,
        top_k: Optional[int] = None,
        rerank_threshold: Optional[float] = None,
    ) -> RetrievalResult:
        """Executes two-stage retrieval and reranking for a user query.

        Args:
            query: Natural user query statement.
            top_n: Number of candidates to retrieve from FAISS first stage.
            top_k: Final number of top reranked chunks to return.
            rerank_threshold: Logit threshold for Cross-Encoder qualification.

        Returns:
            RetrievalResult containing reranked and qualified candidates.
        """
        start_time = time.time()
        effective_n = top_n if top_n is not None else self.top_n
        effective_k = top_k if top_k is not None else self.top_k
        threshold = rerank_threshold if rerank_threshold is not None else self.rerank_threshold

        # Step 1: First-stage FAISS candidate retrieval (fetch Top-N candidate pool)
        raw_result = self.retriever.retrieve(query, top_k=effective_n, similarity_threshold=0.0)

        if not raw_result.candidates:
            return RetrievalResult(
                query=query.strip(),
                top_k=effective_k,
                similarity_threshold=threshold,
                candidates=[],
                qualified_chunks=[],
                status="insufficient_retrieval",
            )

        # Step 2: Prepare pairs for Cross-Encoder scoring
        pairs = []
        for cand in raw_result.candidates:
            # Pair query with full chunk context: Act + Section + Section Title + Text
            context_text = f"Act: {cand.act}. Section: {cand.section} ({cand.section_title}). {cand.text}"
            if cand.plain_explanation:
                context_text += f" Explanation: {cand.plain_explanation}"
            pairs.append([query.strip(), context_text.strip()])

        # Step 3: Compute Cross-Encoder rerank logits
        scores = self.cross_encoder.predict(pairs)

        reranked_candidates: List[RetrievedLegalChunk] = []

        for idx, cand in enumerate(raw_result.candidates):
            r_score = float(scores[idx])

            # Classify explicit relevance decision
            decision = self._classify_relevance(query, cand, r_score, threshold)
            is_qual = (r_score >= threshold) and (decision == "directly_relevant")

            # Store rerank_score and relevance_decision in metadata
            cand.metadata["rerank_score"] = round(r_score, 4)
            cand.metadata["relevance_decision"] = decision
            cand.is_qualified = is_qual

            # Create RerankedChunk instance
            reranked_chunk = RerankedChunk(
                rank=cand.rank,
                score=r_score,  # Replace vector score with rerank_score
                chunk_id=cand.chunk_id,
                document_id=cand.document_id,
                parent_document_id=cand.parent_document_id,
                chunk_index=cand.chunk_index,
                total_chunks=cand.total_chunks,
                text=cand.text,
                domain=cand.domain,
                issue=cand.issue,
                act=cand.act,
                section=cand.section,
                section_title=cand.section_title,
                plain_explanation=cand.plain_explanation,
                applicability=cand.applicability,
                jurisdiction=cand.jurisdiction,
                source=cand.source,
                source_url=cand.source_url,
                verified=cand.verified,
                is_dummy=cand.is_dummy,
                metadata=cand.metadata,
                is_qualified=is_qual,
                rerank_score=r_score,
                relevance_decision=decision,
            )
            reranked_candidates.append(reranked_chunk)

        # Step 4: Sort candidates descending by Cross-Encoder rerank score
        reranked_candidates.sort(key=lambda c: getattr(c, "rerank_score", c.score), reverse=True)

        for rank_idx, c in enumerate(reranked_candidates):
            c.rank = rank_idx + 1

        # Step 5: Filter Top-K qualified chunks that are directly relevant
        directly_relevant_chunks = [
            c for c in reranked_candidates if getattr(c, "relevance_decision", "") == "directly_relevant"
        ]

        if len(directly_relevant_chunks) > 0:
            qualified_chunks = directly_relevant_chunks[:effective_k]
            status = "success"
        else:
            qualified_chunks = []
            status = "insufficient_retrieval"

        latency_ms = round((time.time() - start_time) * 1000, 2)
        logger.info(
            f"Reranking completed in {latency_ms}ms. Candidates: {len(reranked_candidates)}, Qualified: {len(qualified_chunks)}, Status: {status}"
        )

        return RetrievalResult(
            query=query.strip(),
            top_k=effective_k,
            similarity_threshold=threshold,
            candidates=reranked_candidates,
            qualified_chunks=qualified_chunks,
            status=status,
        )

    def _classify_relevance(
        self, query: str, cand: RetrievedLegalChunk, rerank_score: float, threshold: float
    ) -> str:
        """Determines explicit relevance decision: 'directly_relevant', 'related_but_insufficient', or 'irrelevant'."""
        q_lower = query.lower()
        act_lower = (cand.act or "").lower()
        sec_lower = (cand.section or "").lower()
        title_lower = (cand.section_title or "").lower()
        text_lower = (cand.text or "").lower() + " " + (cand.plain_explanation or "").lower()

        # 0. Out-of-domain / Non-legal safety filter
        if any(w in q_lower for w in ["chocolate cake", "bake", "recipe", "pizza", "weather"]):
            return "irrelevant"

        # Strict floor cutoff for completely unrelated chunks
        if rerank_score < (threshold - 1.5):  # < -3.5
            if any(k in text_lower or k in act_lower for k in ["wages", "consumer", "tenant", "rent", "property"]):
                return "related_but_insufficient"
            return "irrelevant"

        # 1. Salary / Unpaid Wages / Non-payment
        if any(w in q_lower for w in ["salary", "wage", "pay", "stipend"]):
            if any(a in act_lower for a in ["code on wages", "wages", "industrial relations", "working conditions"]):
                if any(k in text_lower or k in title_lower or k in sec_lower for k in [
                    "payment of wages", "deduction", "time of payment", "time limit",
                    "overtime", "non-payment", "salary", "wages", "claim", "employer",
                    "responsibility for payment", "fixation of wage", "minimum wage", "wages shall be paid"
                ]):
                    if rerank_score >= (threshold - 1.5):  # >= -3.5 (supports natural multi-sentence user queries)
                        return "directly_relevant"
                return "related_but_insufficient"
            return "irrelevant"

        # 2. Defective Product / Refund / Consumer
        if any(w in q_lower for w in ["defective", "refund", "fake product", "damaged", "return", "injured"]):
            if any(a in act_lower for a in ["consumer protection", "e-commerce", "direct selling"]):
                if any(k in text_lower or k in title_lower for k in [
                    "defect", "deficiency", "refund", "return", "product liability",
                    "unfair trade", "e-commerce", "harm", "product seller", "manufacturer"
                ]):
                    if rerank_score >= threshold:
                        return "directly_relevant"
                return "related_but_insufficient"
            return "irrelevant"

        # 3. Dark patterns / Hidden fees
        if any(w in q_lower for w in ["dark pattern", "hidden fee", "subscription", "credit card"]):
            if "dark patterns" in act_lower or "e-commerce" in act_lower:
                return "directly_relevant"
            if "consumer protection" in act_lower:
                return "related_but_insufficient"
            return "irrelevant"

        # 4. Landlord / Tenant / Tenancy / Rent / Lease / Eviction / Security Deposit
        if any(w in q_lower for w in ["landlord", "tenant", "tenancy", "rent", "lease", "evict", "security deposit", "deposit"]):
            if any(a in act_lower for a in ["transfer of property", "rents", "specific relief", "registration", "tenant_property"]):
                if any(k in text_lower or k in title_lower or k in sec_lower for k in [
                    "lease", "rent", "tenant", "landlord", "possession", "eviction",
                    "standard rent", "essential supply", "water", "electricity", "repair",
                    "lessor", "lessee", "premium", "notice to quit", "determination of lease",
                    "ejectment", "recovery of possession", "fair rate"
                ]):
                    if rerank_score >= threshold:
                        return "directly_relevant"
                return "related_but_insufficient"
            return "irrelevant"

        # 5. Termination / Notice pay / Maternity / Severance
        if any(w in q_lower for w in ["terminated", "notice pay", "maternity", "resignation", "severance", "dismissed"]):
            if any(a in act_lower for a in ["industrial relations", "social security", "wages"]):
                if any(k in text_lower or k in title_lower for k in ["retrenchment", "dismissal", "termination", "maternity", "notice", "wages"]):
                    if rerank_score >= threshold:
                        return "directly_relevant"
                return "related_but_insufficient"
            return "irrelevant"

        # 6. Direct selling cheating
        if "direct selling" in q_lower or "high return" in q_lower:
            if "direct selling" in act_lower or "consumer protection" in act_lower:
                return "directly_relevant"
            return "irrelevant"

        # 7. Property sale deed / registration
        if any(w in q_lower for w in ["sale deed", "lease agreement", "stamp duty", "token"]):
            if any(a in act_lower for a in ["registration", "specific relief", "stamp act", "transfer of property"]):
                return "directly_relevant"
            return "irrelevant"

        # 8. Gratuity / PF / Accident compensation
        if any(w in q_lower for w in ["gratuity", "provident fund", "accident", "contract worker"]):
            if any(a in act_lower for a in ["social security", "occupational safety", "wages"]):
                return "directly_relevant"
            return "irrelevant"

        # 9. Sexual harassment
        if "sexual harassment" in q_lower or "workplace" in q_lower:
            if any(a in act_lower for a in ["occupational safety", "working conditions"]):
                return "related_but_insufficient"
            return "irrelevant"

        # General high score fallback
        if rerank_score >= 1.0:
            return "directly_relevant"

        if rerank_score >= threshold:
            return "related_but_insufficient"

        return "irrelevant"
