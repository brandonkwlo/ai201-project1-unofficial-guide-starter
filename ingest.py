"""Document ingestion — Milestone 3.

Reads the Rate My Professor review files under ``data/`` and turns each
**individual review** into a :class:`Document` with source-attribution metadata
(professor, course, ratings, date, RMP URL). That metadata rides along through
chunking, embedding, and retrieval so the generation step can cite where an
answer came from.

Each file in ``data/`` is one professor and looks like::

    # Ray Klefstad

    **Department:** Computer Science
    **School:** UC Irvine, Irvine, CA
    **Avg Rating:** 2.6 | **Difficulty:** 3.9 | **# Reviews:** 319

    ---

    ## Review #1 — 2026-05-06 21:29:52 +0000 UTC

    **Class:** 141
    **Clarity:** 1 | **Helpful:** 1 | **Difficulty:** 2

    Likes giving unsolicited career advice to the entire class...

    ---

    ## Review #2 — ...

Splitting on the ``## Review #`` boundaries here (structural chunking) means a
review is never merged with an unrelated one. The character-level 350/100
chunking in ``chunk.py`` then only sub-splits the occasional long review.

Run ``python ingest.py`` to print a summary of what was loaded.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

# Filename token (after `reviews_`) -> RMP profile URL, from planning.md.
SOURCE_URLS = {
    "Ziv": "https://www.ratemyprofessors.com/professor/421976",
    "Shindler": "https://www.ratemyprofessors.com/professor/2512998",
    "Klefstad": "https://www.ratemyprofessors.com/professor/17490",
    "Ihler": "https://www.ratemyprofessors.com/professor/1751393",
    "Kask": "https://www.ratemyprofessors.com/professor/2223956",
    "Vazirani": "https://www.ratemyprofessors.com/professor/2763913",
    "Wong-Ma": "https://www.ratemyprofessors.com/professor/2409085",
    "Sudderth": "https://www.ratemyprofessors.com/professor/2285930",
    "Jordan": "https://www.ratemyprofessors.com/professor/240643",
    "Xie": "https://www.ratemyprofessors.com/professor/2127710",
}

_PROF_RE = re.compile(r"^\s*#\s+(.+?)\s*$", re.MULTILINE)
_PROF_STATS_RE = re.compile(
    r"\*\*Avg Rating:\*\*\s*([\d.]+).*?"
    r"\*\*Difficulty:\*\*\s*([\d.]+).*?"
    r"\*\*#\s*Reviews:\*\*\s*(\d+)",
    re.DOTALL,
)
# Splits a file into review blocks; captures the review number that follows.
_REVIEW_SPLIT_RE = re.compile(r"^##\s*Review\s*#(\d+)\s*", re.MULTILINE)
_DATE_RE = re.compile(r"^[—\-\s]*(.+?)\s*$", re.MULTILINE)
_CLASS_RE = re.compile(r"\*\*Class:\*\*\s*(.+)")
_RATINGS_RE = re.compile(
    r"\*\*Clarity:\*\*\s*(\d+)\s*\|\s*"
    r"\*\*Helpful:\*\*\s*(\d+)\s*\|\s*"
    r"\*\*Difficulty:\*\*\s*(\d+)"
)


@dataclass
class Document:
    """A single review plus its source-attribution metadata."""

    professor: str
    source: str
    text: str
    review_number: int
    course: str
    date: str
    clarity: int | None
    helpful: int | None
    difficulty: int | None
    avg_rating: float | None
    path: str

    @property
    def metadata(self) -> dict:
        """Metadata carried onto every chunk (None values dropped for Chroma)."""
        raw = {
            "professor": self.professor,
            "source": self.source,
            "course": self.course,
            "date": self.date,
            "review_number": self.review_number,
            "clarity": self.clarity,
            "helpful": self.helpful,
            "difficulty": self.difficulty,
            "avg_rating": self.avg_rating,
            "path": self.path,
        }
        return {k: v for k, v in raw.items() if v is not None}


def _source_for(path: Path) -> str:
    """Map ``reviews_Wong-Ma.md`` -> the professor's RMP URL."""
    token = path.stem.split("_", 1)[-1]
    return SOURCE_URLS.get(token, "unknown")


def _parse_review_block(raw_number: str, block: str) -> tuple[str, str, str, dict]:
    """Pull date, course, ratings, and body text out of one review block."""
    review_number = int(raw_number)

    # The block is everything after `## Review #N`. First non-empty line is the
    # date (it follows the `—` em dash on the heading line).
    lines = block.splitlines()
    date = ""
    if lines:
        m = _DATE_RE.match(lines[0])
        date = (m.group(1).strip() if m else lines[0].strip()).strip("—- ")

    course_match = _CLASS_RE.search(block)
    course = course_match.group(1).strip() if course_match else ""

    ratings_match = _RATINGS_RE.search(block)
    ratings = {}
    if ratings_match:
        ratings = {
            "clarity": int(ratings_match.group(1)),
            "helpful": int(ratings_match.group(2)),
            "difficulty": int(ratings_match.group(3)),
        }

    # Body: everything after the ratings line, with trailing `---` removed.
    body = block
    if ratings_match:
        body = block[ratings_match.end():]
    elif course_match:
        body = block[course_match.end():]
    body = re.sub(r"\n-{3,}\s*$", "", body.strip()).strip()

    return str(review_number), date, course, {"body": body, **ratings}


def _parse_file(path: Path) -> list[Document]:
    """Parse one professor file into a list of per-review Documents."""
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return []

    prof_match = _PROF_RE.search(raw)
    professor = prof_match.group(1).strip() if prof_match else path.stem
    source = _source_for(path)

    stats = _PROF_STATS_RE.search(raw)
    avg_rating = float(stats.group(1)) if stats else None

    # First split segment is the file header (before Review #1); skip it.
    parts = _REVIEW_SPLIT_RE.split(raw)
    documents: list[Document] = []
    for raw_number, block in zip(parts[1::2], parts[2::2]):
        number_str, date, course, fields = _parse_review_block(raw_number, block)
        body = fields["body"]
        if not body:
            continue
        documents.append(
            Document(
                professor=professor,
                source=source,
                text=body,
                review_number=int(number_str),
                course=course,
                date=date,
                clarity=fields.get("clarity"),
                helpful=fields.get("helpful"),
                difficulty=fields.get("difficulty"),
                avg_rating=avg_rating,
                path=path.name,
            )
        )
    return documents


def load_documents(data_dir: Path | str = DATA_DIR) -> list[Document]:
    """Load every ``.md`` review file in ``data_dir`` into per-review Documents."""
    data_dir = Path(data_dir)
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    documents: list[Document] = []
    for path in sorted(data_dir.glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        parsed = _parse_file(path)
        if not parsed:
            print(f"  ! skipping {path.name}: no reviews found")
            continue
        documents.extend(parsed)
    return documents


if __name__ == "__main__":
    documents = load_documents()
    print(f"Loaded {len(documents)} review(s) from {DATA_DIR}\n")

    by_prof: dict[str, int] = {}
    for doc in documents:
        by_prof[doc.professor] = by_prof.get(doc.professor, 0) + 1
    for professor, count in by_prof.items():
        print(f"  • {professor:<20} {count:>3} review(s)")

    if documents:
        sample = documents[0]
        print(f"\nSample review: {sample.professor} — {sample.course} "
              f"({sample.date})")
        print(f"  {sample.text[:160]}{'…' if len(sample.text) > 160 else ''}")
    else:
        print("  (no reviews found — add .md files to data/)")
