"""Semantic retrieval — Milestone 4 (query step).

Pipeline stage 4 of the architecture diagram:

    Ingestion -> Recursive Chunking -> Embedding + Vector Store -> [Retrieval] -> Generation

Embeds a user query with the same e5 model used at index time (with the
``query:`` prefix) and returns the top-k most similar review chunks from
ChromaDB, each with its source-attribution metadata so the generation step can
cite professors and link back to Rate My Professor.

Top-k = 4 (from planning.md): a sweet spot for this corpus — enough signal even
for professors with only a few reviews, without flooding the prompt with
loosely related chunks.

Run ``python retrieve.py "your question"`` to test retrieval directly.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from embed import embed_query, get_collection

DEFAULT_TOP_K = 4


@dataclass
class RetrievedChunk:
    """A retrieved review chunk plus its similarity score and metadata."""

    text: str
    professor: str
    source: str
    course: str
    score: float  # cosine similarity in [0, 1]; higher is more relevant
    metadata: dict


def retrieve(query: str, top_k: int = DEFAULT_TOP_K) -> list[RetrievedChunk]:
    """Return the top-k review chunks most semantically similar to ``query``."""
    collection = get_collection()
    if collection.count() == 0:
        raise RuntimeError(
            "The vector store is empty. Build it first with: python embed.py"
        )

    results = collection.query(
        query_embeddings=[embed_query(query)],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    retrieved: list[RetrievedChunk] = []
    for text, meta, distance in zip(documents, metadatas, distances):
        retrieved.append(
            RetrievedChunk(
                text=text,
                professor=meta.get("professor", "Unknown"),
                source=meta.get("source", "unknown"),
                course=meta.get("course", ""),
                # Chroma cosine distance = 1 - cosine similarity.
                score=1.0 - distance,
                metadata=meta,
            )
        )
    return retrieved


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) or "Which professor gives the most homework?"
    print(f"Query: {query}\n")
    for i, chunk in enumerate(retrieve(query), start=1):
        course = f" — {chunk.course}" if chunk.course else ""
        print(f"[{i}] {chunk.professor}{course}  (score {chunk.score:.3f})")
        print(f"    {chunk.source}")
        preview = chunk.text[:220] + ("…" if len(chunk.text) > 220 else "")
        print(f"    {preview}\n")
