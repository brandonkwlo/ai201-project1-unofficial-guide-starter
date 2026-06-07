"""Chunking — Milestone 3.

Splits the loaded reviews into overlapping chunks using a recursive character
splitter (the same strategy as LangChain's ``RecursiveCharacterTextSplitter``,
implemented here with no extra dependencies).

``ingest.py`` already splits each professor file into one Document per review,
so most reviews (≤350 chars) pass through as a single chunk. This step only
sub-splits the occasional review that runs longer than the chunk size.

Chunking strategy (from planning.md):
- **Chunk size:** 350 characters — the maximum length of a single Rate My
  Professor review, so a typical review lands in one chunk instead of being
  cut mid-thought.
- **Overlap:** 100 characters — keeps context from spilling across a boundary
  when a longer review or two short ones do get split.

The splitter tries to break on natural boundaries first (blank lines, then
single newlines, then sentences, then spaces) and only falls back to a hard
character cut when no separator fits. Each chunk keeps its parent document's
metadata (professor + source URL) for attribution downstream.

Run ``python chunk.py`` to chunk everything in documents/ and print stats,
including the final chunk count for your planning.md write-up.
"""

from __future__ import annotations

from dataclasses import dataclass

from ingest import Document, load_documents

CHUNK_SIZE = 350
CHUNK_OVERLAP = 100

# Tried in order: paragraph -> line -> sentence -> word -> character.
SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


@dataclass
class Chunk:
    """One chunk of text plus its source attribution metadata."""

    id: str
    text: str
    professor: str
    source: str
    chunk_index: int
    metadata: dict


def _merge_splits(
    splits: list[str], separator: str, chunk_size: int, chunk_overlap: int
) -> list[str]:
    """Greedily combine small splits into ~chunk_size chunks, carrying overlap."""
    sep_len = len(separator)
    chunks: list[str] = []
    current: list[str] = []
    total = 0

    for split in splits:
        added_len = len(split) + (sep_len if current else 0)
        # Emit the current chunk before it would overflow, then slide a window
        # back over the tail so the next chunk overlaps by ~chunk_overlap chars.
        if total + added_len > chunk_size and current:
            chunk = separator.join(current).strip()
            if chunk:
                chunks.append(chunk)
            while total > chunk_overlap and len(current) > 1:
                total -= len(current[0]) + sep_len
                current.pop(0)
        current.append(split)
        total += len(split) + (sep_len if len(current) > 1 else 0)

    tail = separator.join(current).strip()
    if tail:
        chunks.append(tail)
    return chunks


def _split_recursive(
    text: str, separators: list[str], chunk_size: int, chunk_overlap: int
) -> list[str]:
    """Recursively split ``text``, preferring the highest-level separator present."""
    # Pick the first separator that actually occurs in the text.
    separator = separators[-1]
    remaining = separators[-1:]
    for i, sep in enumerate(separators):
        if sep == "":
            separator = sep
            remaining = []
            break
        if sep in text:
            separator = sep
            remaining = separators[i + 1 :]
            break

    splits = list(text) if separator == "" else text.split(separator)

    final: list[str] = []
    good: list[str] = []
    for split in splits:
        if len(split) < chunk_size:
            good.append(split)
            continue
        # `split` is still too big: flush what we have, then recurse on it
        # with finer separators (or hard-cut if none are left).
        if good:
            final.extend(_merge_splits(good, separator, chunk_size, chunk_overlap))
            good = []
        if remaining:
            final.extend(
                _split_recursive(split, remaining, chunk_size, chunk_overlap)
            )
        else:
            final.append(split)
    if good:
        final.extend(_merge_splits(good, separator, chunk_size, chunk_overlap))
    return final


def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
    separators: list[str] | None = None,
) -> list[str]:
    """Split a single string into overlapping chunks."""
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")
    return _split_recursive(
        text, separators or SEPARATORS, chunk_size, chunk_overlap
    )


def chunk_documents(
    documents: list[Document],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[Chunk]:
    """Chunk every document, attaching metadata and a stable id to each chunk."""
    chunks: list[Chunk] = []
    for doc in documents:
        pieces = chunk_text(doc.text, chunk_size, chunk_overlap)
        slug = doc.path.rsplit(".", 1)[0]
        for i, piece in enumerate(pieces):
            chunks.append(
                Chunk(
                    id=f"{slug}::r{doc.review_number}-c{i}",
                    text=piece,
                    professor=doc.professor,
                    source=doc.source,
                    chunk_index=i,
                    metadata={**doc.metadata, "chunk_index": i},
                )
            )
    return chunks


if __name__ == "__main__":
    documents = load_documents()
    chunks = chunk_documents(documents)

    print(f"Documents loaded : {len(documents)}")
    print(f"Total chunks     : {len(chunks)}")
    if chunks:
        sizes = [len(c.text) for c in chunks]
        print(f"Chunk size (chars): min {min(sizes)}, "
              f"avg {sum(sizes) // len(sizes)}, max {max(sizes)}")
        print(f"Settings          : size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP}\n")
        print("Per-professor chunk counts:")
        counts: dict[str, int] = {}
        for c in chunks:
            counts[c.professor] = counts.get(c.professor, 0) + 1
        for professor, n in counts.items():
            print(f"  • {professor:<22} {n:>3} chunk(s)")
        print("\nFirst 5 chunk preview:")
        for first in chunks[:5]:
            print(f"  [{first.id}] ({first.source})")
            print(f"  {first.text[:200]}{'…' if len(first.text) > 200 else ''}")
    else:
        print("(no chunks — add documents to documents/ first)")
