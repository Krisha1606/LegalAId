import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from src.config import config
from src.retriever import LegalRetriever, RetrievedLegalChunk


@dataclass
class GroundedResponse:
    """Represents a grounded legal response produced by the RAG generation pipeline."""

    query: str
    answer: str
    status: str  # "success" | "insufficient_retrieval" | "generation_error"
    retrieval_status: str  # "success" | "insufficient_retrieval"
    qualified_chunk_count: int
    retrieved_chunks: list[dict[str, Any]] = field(default_factory=list)
    sources: list[dict[str, Any]] = field(default_factory=list)
    model_name: str = config.OLLAMA_MODEL

    def to_dict(self) -> dict[str, Any]:
        """Converts grounded response into JSON-serializable dictionary."""
        return {
            "query": self.query,
            "answer": self.answer,
            "status": self.status,
            "retrieval_status": self.retrieval_status,
            "qualified_chunk_count": self.qualified_chunk_count,
            "retrieved_chunks": self.retrieved_chunks,
            "sources": self.sources,
            "model_name": self.model_name,
        }


class LegalPromptBuilder:
    """Constructs deterministic grounded prompts from user query and qualified legal chunks."""

    def build_prompt(self, query: str, chunks: list[RetrievedLegalChunk]) -> str:
        """Constructs prompt containing strict grounding system instructions and retrieved context.

        Args:
            query: User's legal question.
            chunks: List of qualified RetrievedLegalChunk objects.

        Returns:
            Formatted prompt string for Ollama LLM generation.
        """
        context_blocks: list[str] = []
        for idx, chunk in enumerate(chunks, start=1):
            block = (
                f"[Context {idx}]\n"
                f"Chunk ID: {chunk.chunk_id}\n"
                f"Document ID: {chunk.document_id}\n"
                f"Domain: {chunk.domain}\n"
                f"Issue: {chunk.issue}\n"
                f"Act: {chunk.act}\n"
                f"Section: {chunk.section} - {chunk.section_title}\n"
                f"Applicability: {chunk.applicability or 'N/A'}\n"
                f"Jurisdiction: {chunk.jurisdiction or 'N/A'}\n"
                f"Source: {chunk.source or 'N/A'}\n"
                f"Source URL: {chunk.source_url or 'N/A'}\n"
                f"Legal Text:\n{chunk.text}\n"
            )
            context_blocks.append(block)

        context_str = "\n".join(context_blocks)

        prompt = f"""You are an AI Legal Rights Assistant designed to help first-generation litigants understand their legal rights under Indian Law.

SYSTEM INSTRUCTIONS:
1. Answer the user's question ONLY using the provided retrieved legal context below.
2. Do NOT invent, assume, or fabricate any:
   - laws or legislative Acts
   - section numbers or legal provisions
   - monetary penalties, interest rates, or deadlines
   - court procedures or case precedents
   - legal citations, sources, or URLs
3. If the retrieved context does not contain enough information to answer part of the question, explicitly state that the available legal context is insufficient.
4. Do NOT use outside legal knowledge or unprovided legal training memory.
5. Clearly distinguish between what the retrieved legal text states and any plain-language explanation derived directly from that text.
6. Do NOT claim that your response is formal legal advice.
7. Preserve exact Act and Section names from the retrieved context.
8. At the end of your answer, list the relevant retrieved Act and Section citations.

USER QUESTION:
{query.strip()}

RETRIEVED QUALIFIED LEGAL CONTEXT:
{context_str}

GROUNDED RESPONSE:"""
        return prompt


class OllamaClient:
    """Communicates with local Ollama service for LLM text generation."""

    def __init__(
        self,
        model_name: str | None = None,
        base_url: str | None = None,
        timeout: float = 300.0,
    ) -> None:
        """Initializes OllamaClient.

        Args:
            model_name: Ollama model name. Defaults to config.OLLAMA_MODEL.
            base_url: Ollama HTTP base URL. Defaults to config.OLLAMA_BASE_URL.
            timeout: HTTP request timeout in seconds.
        """
        self.model_name = model_name or config.OLLAMA_MODEL
        self.base_url = (base_url or config.OLLAMA_BASE_URL).rstrip("/")
        self.timeout = timeout

    def generate(self, prompt: str) -> str:
        """Sends generation prompt to local Ollama service and returns raw text response.

        Args:
            prompt: Text prompt string.

        Returns:
            Generated response string.

        Raises:
            ValueError: If prompt is empty.
            RuntimeError: If connection fails, model fails, or response is invalid.
        """
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Prompt must be a non-empty string.")

        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Connection": "close",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                resp_bytes = resp.read()
                resp_json = json.loads(resp_bytes.decode("utf-8"))
                text = resp_json.get("response", "")
                if not text:
                    raise RuntimeError("Ollama returned an empty response.")
                return str(text).strip()
        except (
            urllib.error.URLError,
            TimeoutError,
            OSError,
            json.JSONDecodeError,
        ) as e:
            raise RuntimeError(
                f"Failed to communicate with local Ollama service at {url} using model '{self.model_name}': {e}"
            ) from e


from src.retriever import LegalRetriever, RetrievedLegalChunk
from src.reranker import LegalReranker


class LegalGenerator:
    """Main RAG Generation Layer coordinating two-stage reranking retrieval, prompt building, and grounded LLM generation."""

    def __init__(
        self,
        retriever: LegalReranker | LegalRetriever | None = None,
        ollama_client: OllamaClient | None = None,
        prompt_builder: LegalPromptBuilder | None = None,
    ) -> None:
        """Initializes LegalGenerator.

        Args:
            retriever: LegalReranker or LegalRetriever instance. Defaults to new LegalReranker.
            ollama_client: OllamaClient instance. Defaults to new instance.
            prompt_builder: LegalPromptBuilder instance. Defaults to new instance.
        """
        self.retriever = retriever or LegalReranker()
        self.ollama_client = ollama_client or OllamaClient()
        self.prompt_builder = prompt_builder or LegalPromptBuilder()

    @staticmethod
    def extract_source_meta(chunk: RetrievedLegalChunk) -> dict[str, Any]:
        """Extracts complete source traceability metadata dictionary from a retrieved chunk."""
        return {
            "chunk_id": chunk.chunk_id,
            "document_id": chunk.document_id,
            "parent_document_id": chunk.parent_document_id,
            "act": chunk.act,
            "section": chunk.section,
            "section_title": chunk.section_title,
            "source": chunk.source,
            "source_url": chunk.source_url,
            "domain": chunk.domain,
            "issue": chunk.issue,
            "jurisdiction": chunk.jurisdiction,
            "verified": chunk.verified,
            "is_dummy": chunk.is_dummy,
        }

    def generate(
        self,
        query: str,
        top_k: int | None = None,
        similarity_threshold: float | None = None,
    ) -> GroundedResponse:
        """Executes full RAG generation pipeline for a user legal query.

        Args:
            query: User's natural language legal query string.
            top_k: Override Top-K count.
            similarity_threshold: Override similarity score threshold.

        Returns:
            GroundedResponse dataclass.

        Raises:
            ValueError: If query is empty or invalid.
        """
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query must be a non-empty string.")

        if hasattr(self.retriever, "rerank"):
            retrieval_result = self.retriever.rerank(query, top_k=top_k)
        else:
            retrieval_result = self.retriever.retrieve(
                query, top_k=top_k, similarity_threshold=similarity_threshold
            )

        qualified_chunks = retrieval_result.qualified_chunks
        retrieved_chunk_dicts = [c.to_dict() for c in retrieval_result.candidates]

        if retrieval_result.status == "insufficient_retrieval" or len(qualified_chunks) == 0:
            return GroundedResponse(
                query=query.strip(),
                answer=(
                    "I could not find sufficiently relevant legal information in the available "
                    "legal knowledge base to answer this question reliably."
                ),
                status="insufficient_retrieval",
                retrieval_status="insufficient_retrieval",
                qualified_chunk_count=0,
                retrieved_chunks=retrieved_chunk_dicts,
                sources=[],
                model_name=self.ollama_client.model_name,
            )

        prompt = self.prompt_builder.build_prompt(query, qualified_chunks)
        sources = [self.extract_source_meta(c) for c in qualified_chunks]

        try:
            generated_answer = self.ollama_client.generate(prompt)
            return GroundedResponse(
                query=query.strip(),
                answer=generated_answer,
                status="success",
                retrieval_status="success",
                qualified_chunk_count=len(qualified_chunks),
                retrieved_chunks=retrieved_chunk_dicts,
                sources=sources,
                model_name=self.ollama_client.model_name,
            )
        except RuntimeError as e:
            return GroundedResponse(
                query=query.strip(),
                answer=(
                    f"An error occurred while communicating with the local language model: {e}"
                ),
                status="generation_error",
                retrieval_status="success",
                qualified_chunk_count=len(qualified_chunks),
                retrieved_chunks=retrieved_chunk_dicts,
                sources=sources,
                model_name=self.ollama_client.model_name,
            )
