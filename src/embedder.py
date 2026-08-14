from dataclasses import dataclass
from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer

from src.chunker import Chunk
from src.config import config


def build_embedding_text(chunk: Chunk) -> str:
    """Builds a deterministic, structured embedding text representation from a Chunk.

    Includes legal context fields (Act, Section, Section Title, Domain, Issue, Applicability, Legal Text)
    if present without inventing values or altering original chunk.text.

    Args:
        chunk: Chunk object.

    Returns:
        Structured string representation formatted for embedding retrieval.
    """
    parts = []
    if chunk.act:
        parts.append(f"Act: {chunk.act.strip()}")
    if chunk.section:
        parts.append(f"Section: {chunk.section.strip()}")
    if chunk.section_title:
        parts.append(f"Section Title: {chunk.section_title.strip()}")
    if chunk.domain:
        parts.append(f"Domain: {chunk.domain.strip()}")
    if chunk.issue:
        parts.append(f"Issue: {chunk.issue.strip()}")
    if chunk.applicability:
        parts.append(f"Applicability: {chunk.applicability.strip()}")
    if chunk.text:
        parts.append(f"Legal Text: {chunk.text.strip()}")

    return "\n".join(parts)


@dataclass
class EmbeddedChunk:
    """Represents a legal chunk associated with its vector embedding."""

    chunk_id: str
    document_id: str
    embedding: np.ndarray
    embedding_dimension: int
    chunk: Chunk

    def to_dict(self) -> dict[str, Any]:
        """Converts embedded chunk to dictionary representation (embedding truncated for serialization)."""
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "embedding_dimension": self.embedding_dimension,
            "embedding_dtype": str(self.embedding.dtype),
            "embedding_prefix": self.embedding[:5].tolist() if self.embedding is not None else [],
            "chunk": self.chunk.to_dict(),
        }


class LegalEmbedder:
    """Modular embedding layer using SentenceTransformers for legal chunks and queries."""

    def __init__(
        self,
        model_name: str | None = None,
        normalize_embeddings: bool = True,
    ) -> None:
        """Initializes the embedder with the configured SentenceTransformer model.

        Args:
            model_name: Model identifier or path. Defaults to config.EMBEDDING_MODEL.
            normalize_embeddings: Whether to L2-normalize vector outputs.
        """
        self.model_name = model_name or config.EMBEDDING_MODEL
        self.normalize_embeddings = normalize_embeddings
        self._model = SentenceTransformer(self.model_name)

        self.embedding_dimension: int = int(self._model.get_embedding_dimension())

    def embed_text(self, text: str) -> np.ndarray:
        """Embeds a single string into a 1D float32 vector array.

        Args:
            text: Raw string to embed.

        Returns:
            1D numpy array of shape (embedding_dimension,) with dtype float32.
        """
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Input text to embed must be a non-empty string.")

        vec = self._model.encode(
            text,
            normalize_embeddings=self.normalize_embeddings,
            convert_to_numpy=True,
        )
        vec = vec.astype(np.float32)
        if vec.ndim == 2:
            vec = vec[0]

        if vec.shape[0] != self.embedding_dimension:
            raise ValueError(
                f"Embedding dimension mismatch: expected {self.embedding_dimension}, got {vec.shape[0]}"
            )

        return vec

    def embed_texts(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        """Embeds a list of strings into a 2D float32 vector matrix.

        Args:
            texts: List of strings.
            batch_size: Processing batch size.

        Returns:
            2D numpy array of shape (N, embedding_dimension) with dtype float32.
        """
        if not texts:
            return np.empty((0, self.embedding_dimension), dtype=np.float32)

        for i, t in enumerate(texts):
            if not isinstance(t, str) or not t.strip():
                raise ValueError(f"Text at index {i} must be a non-empty string.")

        matrix = self._model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=self.normalize_embeddings,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        matrix = matrix.astype(np.float32)

        if matrix.shape[1] != self.embedding_dimension:
            raise ValueError(
                f"Embedding dimension mismatch: expected {self.embedding_dimension}, got {matrix.shape[1]}"
            )

        return matrix

    def embed_chunk(self, chunk: Chunk) -> EmbeddedChunk:
        """Embeds a single Chunk object.

        Args:
            chunk: Chunk instance.

        Returns:
            EmbeddedChunk object containing float32 vector.
        """
        embed_input = build_embedding_text(chunk)
        vector = self.embed_text(embed_input)

        return EmbeddedChunk(
            chunk_id=chunk.chunk_id,
            document_id=chunk.document_id,
            embedding=vector,
            embedding_dimension=self.embedding_dimension,
            chunk=chunk,
        )

    def embed_chunks(self, chunks: list[Chunk], batch_size: int = 32) -> list[EmbeddedChunk]:
        """Embeds a list of Chunk objects in batches, guaranteeing 1-to-1 order preservation.

        Args:
            chunks: List of Chunk objects.
            batch_size: Processing batch size.

        Returns:
            List of EmbeddedChunk objects in exact order of input chunks.
        """
        if not chunks:
            return []

        embed_inputs = [build_embedding_text(c) for c in chunks]
        matrix = self.embed_texts(embed_inputs, batch_size=batch_size)

        embedded_chunks: list[EmbeddedChunk] = []
        for i, chunk in enumerate(chunks):
            vec = matrix[i]
            embedded_chunks.append(
                EmbeddedChunk(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    embedding=vec,
                    embedding_dimension=self.embedding_dimension,
                    chunk=chunk,
                )
            )

        return embedded_chunks

    def embed_query(self, query: str) -> np.ndarray:
        """Embeds a user query string using the SAME model and normalization behavior.

        Args:
            query: User search query string.

        Returns:
            1D numpy array of shape (embedding_dimension,) with dtype float32.
        """
        return self.embed_text(query)
