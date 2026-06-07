"""Gradio interface — Milestone 5 (interface step).

The front door to the full pipeline: a user types a question, and this wires
together retrieval (e5 + ChromaDB) and grounded generation (Groq
``llama-3.3-70b-versatile``), then shows the answer with its cited sources.

Run ``python app.py`` and open the printed local URL. Build the vector store
first with ``python embed.py`` if you haven't already.
"""

from __future__ import annotations

import gradio as gr

from embed import get_collection
from generate import answer, format_sources

EXAMPLE_QUESTIONS = [
    "Which professor gives the most homework?",
    "Which professor has the best teaching style?",
    "Does Professor Klefstad give weekly quizzes?",
    "Which professor is the easiest?",
    "Which professor at UCI is the most recommended?",
]


def _index_is_ready() -> bool:
    try:
        return get_collection().count() > 0
    except Exception:
        return False


def respond(query: str) -> tuple[str, str]:
    """Run one query through the pipeline and return (answer, sources) markdown."""
    query = (query or "").strip()
    if not query:
        return "Please enter a question.", ""

    if not _index_is_ready():
        return (
            "⚠️ The vector store is empty. Run `python embed.py` to build the "
            "index, then reload this page.",
            "",
        )

    try:
        result = answer(query)
    except Exception as exc:  # surface config errors (e.g. missing API key) in-UI
        return f"⚠️ {exc}", ""

    if not result.sources:
        return result.text, ""

    sources_md = "### Sources\n" + "\n".join(
        f"- {line}" for line in format_sources(result.sources).splitlines()
    )
    return result.text, sources_md


with gr.Blocks(title="The Unofficial Guide — UCI CS Professors") as demo:
    gr.Markdown(
        "# 🎓 The Unofficial Guide\n"
        "Ask about UC Irvine CS professors. Answers come **only** from student "
        "reviews on Rate My Professor, with sources cited below each answer."
    )

    query_box = gr.Textbox(
        label="Your question",
        placeholder="e.g. Does Professor Klefstad give weekly quizzes?",
        lines=2,
    )
    ask_button = gr.Button("Ask", variant="primary")

    answer_box = gr.Markdown(label="Answer")
    sources_box = gr.Markdown(label="Sources")

    gr.Examples(examples=EXAMPLE_QUESTIONS, inputs=query_box)

    ask_button.click(respond, inputs=query_box, outputs=[answer_box, sources_box])
    query_box.submit(respond, inputs=query_box, outputs=[answer_box, sources_box])


if __name__ == "__main__":
    demo.launch()
