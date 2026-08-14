import json
from pathlib import Path
from typing import Any

import faiss
import numpy as np

from src.config import config
from src.embedder import EmbeddedChunk


class FAISSVectorStore:
    """Modular FAISS Vector Store managing L2-normalized float32 vectors and persistent metadata mappings."""

    def __init__(self, dir_path: str | Path | None = None) -> None:
        """Initializes the vector store directory.

        Args:
            dir_path: Path to vector store directory. Defaults to config.VECTOR_STORE_PATH.
        """
        self.dir_path = Path(dir_path) if dir_path is not None else Path(config.VECTOR_STORE_PATH)
        self.index: faiss.Index | None = None
        self.dimension: int | None = None
        self.metadata_map: dict[str, dict[str, Any]] = {}

    @property
    def ntotal(self) -> int:
        """Returns the total number of vectors in the FAISS index."""
        return self.index.ntotal if self.index is not None else 0

    def build_index(self, embedded_chunks: list[EmbeddedChunk]) -> None:
        """Builds a FAISS IndexFlatIP index and position-to-metadata mapping from embedded chunks.

        Args:
            embedded_chunks: List of EmbeddedChunk objects.

        Raises:
            ValueError: If input list is empty, contains duplicate chunk IDs, or has inconsistent dimensions.
            TypeError: If input embeddings are not NumPy arrays.
        """
        if not embedded_chunks:
            raise ValueError("Cannot build FAISS index from an empty list of embedded chunks.")

        seen_ids = set()
        for i, ec in enumerate(embedded_chunks):
            if not isinstance(ec, EmbeddedChunk):
                raise TypeError(
                    f"Item at index {i} must be an EmbeddedChunk, got {type(ec).__name__}."
                )
            if not ec.chunk_id:
                raise ValueError(f"EmbeddedChunk at index {i} is missing chunk_id.")
            if ec.chunk_id in seen_ids:
                raise ValueError(
                    f"Duplicate chunk_id detected: '{ec.chunk_id}'. Chunk IDs must be unique."
                )
            seen_ids.add(ec.chunk_id)

        dimension = embedded_chunks[0].embedding_dimension
        for i, ec in enumerate(embedded_chunks):
            if not isinstance(ec.embedding, np.ndarray):
                raise TypeError(f"Embedding at index {i} must be a numpy.ndarray.")
            if ec.embedding.shape[0] != dimension:
                raise ValueError(
                    f"Embedding dimension mismatch at index {i}: expected {dimension}, got {ec.embedding.shape[0]}"
                )

        index = faiss.IndexFlatIP(dimension)

        matrix = np.array([ec.embedding for ec in embedded_chunks], dtype=np.float32)
        index.add(matrix)

        metadata_dict: dict[str, dict[str, Any]] = {}
        for pos, ec in enumerate(embedded_chunks):
            metadata_dict[str(pos)] = ec.chunk.to_dict()

        self.index = index
        self.dimension = dimension
        self.metadata_map = metadata_dict

    def save(self, dir_path: str | Path | None = None) -> tuple[Path, Path]:
        """Saves the FAISS index binary and metadata JSON to disk.

        Args:
            dir_path: Target directory path. Defaults to self.dir_path.

        Returns:
            Tuple of (index_file_path, metadata_file_path).

        Raises:
            ValueError: If no index has been built or loaded.
        """
        if self.index is None or self.dimension is None:
            raise ValueError("Cannot save an uninitialized or empty FAISS vector store.")

        target_dir = Path(dir_path) if dir_path is not None else self.dir_path
        target_dir.mkdir(parents=True, exist_ok=True)

        index_path = target_dir / "index.faiss"
        metadata_path = target_dir / "metadata.json"

        faiss.write_index(self.index, str(index_path))

        payload = {
            "faiss_index_type": type(self.index).__name__,
            "dimension": self.dimension,
            "ntotal": self.ntotal,
            "positions": self.metadata_map,
        }
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return index_path, metadata_path

    def load(self, dir_path: str | Path | None = None) -> None:
        """Loads FAISS index binary and metadata JSON from disk and validates position continuity.

        Args:
            dir_path: Directory path containing index.faiss and metadata.json. Defaults to self.dir_path.

        Raises:
            FileNotFoundError: If index.faiss or metadata.json is missing.
            ValueError: If vector count does not match metadata count or positions are non-contiguous.
        """
        target_dir = Path(dir_path) if dir_path is not None else self.dir_path
        index_path = target_dir / "index.faiss"
        metadata_path = target_dir / "metadata.json"

        if not index_path.is_file():
            raise FileNotFoundError(f"FAISS index file not found at: {index_path.resolve()}")
        if not metadata_path.is_file():
            raise FileNotFoundError(
                f"Metadata mapping file not found at: {metadata_path.resolve()}"
            )

        index = faiss.read_index(str(index_path))

        with open(metadata_path, encoding="utf-8") as f:
            payload = json.load(f)

        dimension = payload.get("dimension", index.d)
        positions = payload.get("positions", {})

        if index.ntotal != len(positions):
            raise ValueError(
                f"FAISS vector count ({index.ntotal}) does not match metadata records count ({len(positions)})."
            )

        for pos in range(index.ntotal):
            pos_str = str(pos)
            if pos_str not in positions:
                raise ValueError(
                    f"Missing contiguous metadata position key: '{pos_str}' in {metadata_path.resolve()}"
                )

        self.index = index
        self.dimension = int(dimension)
        self.metadata_map = positions

    def get_chunk_by_position(self, position: int) -> dict[str, Any]:
        """Returns metadata dictionary for a specified FAISS position index.

        Args:
            position: Vector index position (0..ntotal-1).

        Returns:
            Metadata dictionary.

        Raises:
            IndexError: If position is out of bounds.
        """
        pos_str = str(position)
        if pos_str not in self.metadata_map:
            raise IndexError(
                f"Position index {position} out of bounds for store with {self.ntotal} records."
            )
        return self.metadata_map[pos_str]

    def search_raw_vector(
        self, query_vector: np.ndarray, top_k: int = 5
    ) -> tuple[np.ndarray, np.ndarray]:
        """Low-level vector search helper used ONLY for internal index validation.

        Args:
            query_vector: 1D or 2D float32 numpy array.
            top_k: Number of nearest neighbors to retrieve.

        Returns:
            Tuple of (distances matrix, position_indices matrix).

        Raises:
            ValueError: If vector store is empty or query vector dimension does not match.
        """
        if self.index is None or self.dimension is None:
            raise ValueError("Cannot search an uninitialized or empty FAISS vector store.")

        vec = np.asarray(query_vector, dtype=np.float32)
        if vec.ndim == 1:
            vec = np.expand_dims(vec, axis=0)

        if vec.shape[1] != self.dimension:
            raise ValueError(
                f"Query vector dimension mismatch: expected {self.dimension}, got {vec.shape[1]}"
            )

        distances, indices = self.index.search(vec, top_k)
        return distances, indices
