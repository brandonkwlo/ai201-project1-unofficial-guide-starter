"""Embedding + vector store — Milestone 4 (build step).

Pipeline stage 3 of the architecture diagram:

    Ingestion -> Recursive Chunking -> [Embedding + Vector Store] -> Retrieval -> Generation

Takes the chunks produced by ``chunk_documents()`` (one chunk per review, with
professor/course/rating/source metadata), embeds them with
``intfloat/e5-base-v2``, and stores them in a persistent ChromaDB collection so
retrieval doesn't re-embed on every query.

Why e5-base-v2 (from planning.md): strong open-source model specialised for
short, opinion/review-style text, with a 512-token limit that comfortably fits
350-character reviews and runs locally (no API cost or latency).

**Important e5 detail:** the model is trained with prefixes. Documents must be
embedded as ``"passage: <text>"`` and queries as ``"query: <text>"`` — mixing
them up quietly degrades retrieval quality. Those prefixes are applied here and
in ``embed_query`` so the build and query sides always agree.

Run ``python embed.py`` to (re)build the index.
"""

from __future__ import annotations

from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from chunk import chunk_documents
from ingest import load_documents

EMBED_MODEL = "intfloat/e5-base-v2"
COLLECTION_NAME = "rmp_reviews"
CHROMA_DIR = Path(__file__).parent / "chroma_db"

_model: SentenceTransformer | None = None


def get_embedder() -> SentenceTransformer:
    """Load the e5 model once and reuse it (it's ~440MB; loading is slow)."""
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL)
    return _model


def embed_passages(texts: list[str], show_progress: bool = False) -> list[list[float]]:
    """Embed documents for storage (e5 'passage:' prefix, normalized vectors)."""
    model = get_embedder()
    prefixed = [f"passage: {t}" for t in texts]
    vectors = model.encode(
        prefixed, normalize_embeddings=True, show_progress_bar=show_progress
    )
    return vectors.tolist()


def embed_query(text: str) -> list[float]:
    """Embed a search query (e5 'query:' prefix, normalized vector)."""
    model = get_embedder()
    vector = model.encode([f"query: {text}"], normalize_embeddings=True)[0]
    return vector.tolist()


def get_client() -> chromadb.ClientAPI:
    """Persistent Chroma client backed by the gitignored chroma_db/ folder."""
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def get_collection() -> chromadb.Collection:
    """Return the reviews collection, creating it if it doesn't exist.

    Cosine space is used because e5 vectors are normalized, so cosine
    similarity is the right distance for nearest-neighbour search.
    """
    return get_client().get_or_create_collection(
        COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
    )


def build_index(rebuild: bool = True) -> chromadb.Collection:
    """Embed all chunks and (re)populate the Chroma collection."""
    chunks = chunk_documents(load_documents())
    if not chunks:
        raise RuntimeError("No chunks to index — check that data/ has review files.")

    client = get_client()
    if rebuild:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass  # nothing to delete on a fresh run

    collection = client.get_or_create_collection(
        COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
    )

    print(f"Embedding {len(chunks)} chunk(s) with {EMBED_MODEL} …")
    embeddings = embed_passages([c.text for c in chunks], show_progress=True)

    collection.add(
        ids=[c.id for c in chunks],
        documents=[c.text for c in chunks],
        embeddings=embeddings,
        metadatas=[c.metadata for c in chunks],
    )
    return collection


if __name__ == "__main__":
    collection = build_index(rebuild=True)
    print(f"\nIndexed {collection.count()} chunk(s) into '{COLLECTION_NAME}'")
    print(f"Persisted to {CHROMA_DIR}")
