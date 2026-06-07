"""Grounded generation — Milestone 5 (generation step).

Pipeline stage 5 of the architecture diagram:

    Ingestion -> Chunking -> Embedding + Vector Store -> Retrieval -> [Generation]

Takes the top-k review chunks from ``retrieve()`` and asks Groq's
``llama-3.3-70b-versatile`` to answer **only** from those chunks, with source
attribution back to each professor's Rate My Professor page.

Grounding is enforced two ways:
1. **System prompt** — the model is instructed to answer strictly from the
   numbered context, to say it doesn't have enough information when the context
   is silent, and to cite the [n] sources it used.
2. **Structure** — every chunk is passed as a numbered block tagged with the
   professor, course, and RMP URL, so the model has explicit, attributable
   evidence to cite and nothing else to draw on. Temperature is low to keep it
   from improvising beyond the text.

``answer(query)`` returns the grounded answer plus the sources used.
``python generate.py "your question"`` runs one query end-to-end.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass

from dotenv import load_dotenv
from groq import Groq

from retrieve import DEFAULT_TOP_K, RetrievedChunk, retrieve

load_dotenv()

GROQ_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """\
You are The Unofficial Guide, a helpful assistant that answers questions about \
UC Irvine Computer Science professors using ONLY student reviews from Rate My \
Professor that are provided to you as context.

Rules:
- Answer strictly from the numbered review excerpts in the context. Do not use \
outside knowledge or make assumptions beyond what the reviews say.
- If the context does not contain enough information to answer, say so plainly \
(e.g., "The reviews provided don't say enough to answer that") instead of \
guessing.
- These are subjective student opinions, not facts — reflect disagreement when \
reviews conflict, and don't overstate a single review as the consensus.
- Cite the reviews you used with bracketed numbers like [1], [2] that match the \
context. Attribute claims to the professor named in that excerpt.
- Be concise and specific. Quote short phrases from reviews when useful."""

NO_CONTEXT_MESSAGE = (
    "I couldn't find any relevant reviews for that question. Try asking about a "
    "specific professor, course, workload, exams, or teaching style."
)


@dataclass
class Answer:
    """A grounded answer plus the chunks that grounded it."""

    text: str
    sources: list[RetrievedChunk]


_client: Groq | None = None


def get_client() -> Groq:
    """Create the Groq client once, reading GROQ_API_KEY from the environment."""
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key or api_key == "your_key_here":
            raise RuntimeError(
                "GROQ_API_KEY is not set. Copy .env.example to .env and add your "
                "free key from https://console.groq.com"
            )
        _client = Groq(api_key=api_key)
    return _client


def format_context(chunks: list[RetrievedChunk]) -> str:
    """Render retrieved chunks as numbered, attributable evidence blocks."""
    blocks = []
    for i, chunk in enumerate(chunks, start=1):
        course = f", {chunk.course}" if chunk.course else ""
        blocks.append(
            f"[{i}] Professor {chunk.professor}{course} "
            f"(source: {chunk.source})\n{chunk.text}"
        )
    return "\n\n".join(blocks)


def answer(query: str, top_k: int = DEFAULT_TOP_K) -> Answer:
    """Retrieve context for ``query`` and generate a grounded, cited answer."""
    chunks = retrieve(query, top_k=top_k)
    if not chunks:
        return Answer(text=NO_CONTEXT_MESSAGE, sources=[])

    user_prompt = (
        f"Context (student reviews):\n\n{format_context(chunks)}\n\n"
        f"Question: {query}\n\n"
        "Answer using only the reviews above, and cite them with [n]."
    )

    response = get_client().chat.completions.create(
        model=GROQ_MODEL,
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    return Answer(text=response.choices[0].message.content, sources=chunks)


def format_sources(chunks: list[RetrievedChunk]) -> str:
    """Render a deduplicated, numbered source list for display under an answer."""
    lines = []
    for i, chunk in enumerate(chunks, start=1):
        course = f" — {chunk.course}" if chunk.course else ""
        lines.append(
            f"[{i}] {chunk.professor}{course} "
            f"(relevance {chunk.score:.2f}) — {chunk.source}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) or "Does Professor Klefstad give weekly quizzes?"
    result = answer(query)
    print(f"Q: {query}\n")
    print(result.text)
    if result.sources:
        print("\nSources:")
        print(format_sources(result.sources))
