# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section _after_ you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] — useful because official
     course descriptions don't reflect teaching style, exam difficulty, or workload." -->

My system covers University of California Irvine (UCI) Computer Science professor reviews. It is useful because it dives deeper into the inner workings of the courses such as difficulty, workload, and the teaching style of the professor from the perspective of the student. Also, it helps the student determine whether they want to enroll in a course with said professor.

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

Sources are all from Rate My Professor where it collects student reviews based on the professor and course they were teaching.

- Hadar Ziv https://www.ratemyprofessors.com/professor/421976
- Michael Shindler https://www.ratemyprofessors.com/professor/2512998
- Raymond Klefstad https://www.ratemyprofessors.com/professor/17490
- Alexander Ihler https://www.ratemyprofessors.com/professor/1751393
- Kalev Kask https://www.ratemyprofessors.com/professor/2223956
- Vijay Vazirani https://www.ratemyprofessors.com/professor/2763913
- Jennifer Wong-Ma https://www.ratemyprofessors.com/professor/2409085
- Erik Sudderth https://www.ratemyprofessors.com/professor/2285930
- Scott Jordan https://www.ratemyprofessors.com/professor/240643
- Xiaohui Xie https://www.ratemyprofessors.com/professor/2127710

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:**
The chunk size used was 350 characters, as that closely matches the
maximum length of a single Rate My Professor review. This ensures
each chunk captures roughly one complete review without bundling
multiple reviews together, keeping retrieved chunks semantically
focused on a single professor/course experience.

**Overlap:**
An overlap of 100 characters was used because at 350 characters per
chunk, reviews can get split mid-sentence at boundaries. The 100
character overlap repeats the tail of the previous chunk at the start
of the next, ensuring no boundary sentence loses its meaning. This is
especially important given how short and conversational RMP reviews
are, where a single sentence can carry the entire sentiment.

**Why these choices fit your documents:**
RMP reviews are short, informal, and self-contained — one review
rarely depends on another for meaning. A 350 character chunk respects
that natural boundary, and the 100 character overlap guards against
the high boundary-split risk that comes with such a small chunk size.

**Final chunk count:**
184

**Sample chunks:**

| #   | Source file           | Professor / Course             | Chunk text                                                                                                                                                                                                                                                                                                                                                     |
| --- | --------------------- | ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `reviews_Ihler.md`    | Alexander Ihler / CS273A       | "He's okay, but he's the most disorganized professor I've ever seen here. He barely prepares for class, so you won't learn much from the lectures. The midterm and final have the same structure as the previous tests, though, which helps a bit."                                                                                                            |
| 2   | `reviews_Jordan.md`   | Scott A. Jordan / CS132        | "Oddly, one TA made my Ed post private when I asked for hints for one of the problem sets; should have stayed public to help everyone else. Midterm/Final graded based on professor judgement + custom cutoffs, averages were 55 and 60 respectively. Midterm too focused on calculations, Final was better (which was where I made a big comeback, an A) 3/3" |
| 3   | `reviews_Kask.md`     | Kalev Kask / CS171             | "Lectures can be boring but clearly cares about his students and is very understanding. No midterm but 4 quizzes worth 10% of your grade bi-weekly. Very doable and extremely similar to discussion slides. Gives lots of extra credit for class participation, workload is very reasonable. Overall nice person and a good professor, would take him again."  |
| 4   | `reviews_Klefstad.md` | Ray Klefstad / 141             | "Likes giving unsolicited career advice to the entire class. Misogynistic remarks and rude comments occasionally. His quizzes are fair, but the way he grades the final is questionable."                                                                                                                                                                      |
| 5   | `reviews_Shindler.md` | Michael Shindler / COMPSCI260P | "I'm glad to take this class, learnt a lot. Got a good grade, participation is the key. Shindler does research in algorithms, and he does care to make students understand his lectures."                                                                                                                                                                      |

(Generated with `python chunk.py`; each chunk is one review, tagged with its source file and professor/course metadata.)

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:**
The embedding model chosen is `intfloat/e5-base-v2`, an open-source
model that runs locally without API costs. It is well-suited for this
project because it performs strongly on short, sentence-level text —
which aligns with Rate My Professor reviews being brief and
conversational. Since all chunks are ~350 characters, the model's
context length is never stressed, and its balance of speed and
accuracy makes it practical for a local pipeline.

**Production tradeoff reflection:**
If deploying for real users, I would weigh the following tradeoffs:

- **Accuracy on domain-specific text** — RMP reviews are informal
  and slang-heavy. A general-purpose model like e5-base-v2 may
  struggle with phrases like "easy A" or "tough grader." A
  fine-tuned or larger model like `text-embedding-3-large`
  (OpenAI) may retrieve more accurately.
- **Latency** — e5-base-v2 runs locally, which avoids network
  latency but is bottlenecked by local hardware. An API-hosted
  model offloads compute but introduces network dependency.
- **Context length** — If chunk sizes were increased, e5-base-v2's
  512 token limit could become a constraint, whereas models like
  `text-embedding-3-large` handle longer inputs more gracefully.
- **Multilingual support** — e5-base-v2 is English-optimized. If
  the user base includes non-English speakers or reviews in other
  languages, a multilingual model like `paraphrase-multilingual`
  would be necessary.

## Retrieval Test Results

Run with `python retrieve.py "<query>"` (top-k = 3 shown).

**Query 1: "Does Professor Klefstad give weekly quizzes?"**

| Rank | Professor / Course       | Score | Chunk (excerpt)                                                                           |
| ---- | ------------------------ | ----- | ----------------------------------------------------------------------------------------- |
| 1    | Ray Klefstad / 141       | 0.867 | "Lots of quizzes, labs, and homework, one of each every week (quiz in person)…"           |
| 2    | Ray Klefstad / CS141     | 0.860 | "Klefstad is such a funny professor… Lots of busywork reading/really difficult homework…" |
| 3    | Michael Shindler / CS162 | 0.851 | "The Lebron James of UCI professors. Klefstad is Micheal Jorfraud"                        |

_Why these are relevant:_ Ranks 1–2 are direct hits — both are Klefstad reviews that explicitly describe weekly, in-person quizzes, which is exactly what the query asks. Rank 3 is a false positive that's still explainable: it literally contains the token "Klefstad," so it embeds near the query, even though it's a joke review posted on Shindler's page (the cross-attribution issue documented in Failure Case Analysis).

**Query 2: "How hard are Kalev Kask exams?"**

| Rank | Professor / Course | Score | Chunk (excerpt)                                                                                                                     |
| ---- | ------------------ | ----- | ----------------------------------------------------------------------------------------------------------------------------------- |
| 1    | Kalev Kask / CS271 | 0.871 | "Kask is very nice. The project was by far the hardest part of the course. The quizzes were pretty easy and there was no homework…" |
| 2    | Kalev Kask / CS171 | 0.827 | "I would definitely say Kask is definitely the definition of an 'okay' professor…"                                                  |
| 3    | Kalev Kask / CS171 | 0.826 | "Just watch the discussions to do well on the tests. Group project was pretty unorganized…"                                         |

_Why these are relevant:_ All three chunks are Kalev Kask reviews, and each speaks to assessment difficulty — quiz/exam ease, how to study for tests, and where the real difficulty lies (the project, not the exams). The embedding model correctly isolated the one professor named in the query and surfaced the workload/exam-related reviews rather than unrelated ones.

**Query 3: "Which professor has the best teaching style?"**

| Rank | Professor / Course       | Score | Chunk (excerpt)                                                                                         |
| ---- | ------------------------ | ----- | ------------------------------------------------------------------------------------------------------- |
| 1    | Jennifer Wong-Ma / ICS51 | 0.833 | "Prof. Wong-Ma is an exceptional lecturer. This was probably the most organized class i've ever taken…" |
| 2    | Michael Shindler / CS162 | 0.829 | "The Lebron James of UCI professors. Klefstad is Micheal Jorfraud"                                      |
| 3    | Jennifer Wong-Ma / ICS51 | 0.826 | "Prof. Wong-ma is one of the best professors I've ever had. Her course is very well organized…"         |

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**
Grounding is enforced primarily through the system prompt in generate.py, which instructs the model to "answer strictly from the numbered review excerpts in the context" and to "not use outside knowledge or make assumptions beyond what the reviews say." It also tells the model that if the context doesn't contain enough information, it must say so plainly instead of guessing — this is what makes the system refuse off-topic questions (e.g. it declined a question about pizza places near campus because no review mentioned them). Structurally, I reinforce this by only ever passing the top-4 retrieved review chunks into the prompt as numbered, attributed blocks, and by running the model at a low temperature (0.2) so it stays close to the source text rather than improvising.

**How source attribution is surfaced in the response:**
Attribution happens at two levels. First, each retrieved chunk is injected into the prompt as a numbered block tagged with the professor, course, and Rate My Professor URL, and the prompt requires the model to cite the reviews it used with bracketed markers like [1], [2] inside its answer. Second, the Gradio interface (app.py) renders a separate "Sources" section beneath every answer that lists each cited chunk's professor, course, relevance score, and a link back to the original RMP page, so a user can click through and verify the claim against the actual reviews.

**Example responses:**

Run with `python generate.py "<query>"` (answer + Sources panel shown).

**Example 1 (grounded):**

> **Q:** Does Professor Klefstad give weekly quizzes?
>
> **A:** Yes, according to the reviews, Professor Klefstad gives weekly quizzes. This is mentioned in reviews [1] and [4], with [1] stating "one of each every week (quiz in person)" and [4] mentioning "absurdly specific weekly quizzes".
>
> **Sources:**
> [1] Ray Klefstad — 141 (relevance 0.87) — https://www.ratemyprofessors.com/professor/17490
> [2] Ray Klefstad — CS141 (relevance 0.86) — https://www.ratemyprofessors.com/professor/17490
> [3] Michael Shindler — CS162 (relevance 0.85) — https://www.ratemyprofessors.com/professor/2512998
> [4] Ray Klefstad — ICS46 (relevance 0.84) — https://www.ratemyprofessors.com/professor/17490

**Example 2 (grounded, reflects mixed reviews):**

> **Q:** How hard are Kalev Kask exams?
>
> **A:** The reviews provide mixed information… [1] mentions "The quizzes were pretty easy" for CS271, and [4] notes the weekly quizzes and final were online with 2 attempts, suggesting the exams are not very challenging. The project, not the exams, was described as "by far the hardest part of the course" [1].
>
> **Sources:**
> [1] Kalev Kask — CS271 (relevance 0.87) — https://www.ratemyprofessors.com/professor/2223956
> [2] Kalev Kask — CS171 (relevance 0.83) — https://www.ratemyprofessors.com/professor/2223956
> [3] Kalev Kask — CS171 (relevance 0.83) — https://www.ratemyprofessors.com/professor/2223956
> [4] Kalev Kask — CS171 (relevance 0.82) — https://www.ratemyprofessors.com/professor/2223956

**Out-of-scope query (refusal):**

> **Q:** What is the best pizza place near campus?
>
> **A:** The reviews provided don't say enough to answer that. They discuss professors and their classes, but do not mention pizza places near campus.

This shows the grounding guardrail working: the question is off-domain, so the system declines instead of inventing an answer.

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| #   | Question                                        | Expected answer                                              | System response (summarized)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | Retrieval quality | Response accuracy |
| --- | ----------------------------------------------- | ------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------- | ----------------- |
| 1   | Which professor is the easiest?                 | Reviews will vary depending on the student                   | According to the reviews, Professor Hadar Ziv's class is described as "Unbelievably easy" [1] and has a "pretty fair/easy" class structure [4]. In contrast, Professor Erik Sudderth's class has easy tests if you understand the concepts, but the lectures are hard to understand [2]. Professor Michael Shindler's review doesn't mention the ease of the class [3]. Therefore, based on the reviews, Professor Hadar Ziv's class appears to be the easiest [1, 4].                                                                                                                                                                                                                               | Relevant          | Accurate          |
| 2   | Which professor gives the most homework?        | Reviews will either say Raymond Klefstad or Jennifer Wong-Ma | According to the reviews, Professor Erik Sudderth's CS177 class has weekly homework that "can easily take up 10 hours to complete" [3]. This suggests that Professor Sudderth gives a significant amount of homework. In contrast, the reviews for Professor Scott A. Jordan [1] and Professor Alexander Ihler [4] mention homework, but do not specify the time commitment required. Professor Erik Sudderth's other review [2] mentions that homework assignments are "straight forward" if you watch lecture and look for hints, but still implies a notable time commitment. Based on the information provided, Professor Erik Sudderth appears to give the most homework [3].                   | Relevant          | Accurate          |
| 3   | Which professor has the best teaching style?    | Reviews with say either Michael Shindler or Jennifer Wong-Ma | According to the reviews, Professor Jennifer Wong-Ma [1], [3] is praised for her exceptional lecturing style, making the class "fun and provides a healthy environment to learn" [1] and having "engaging lectures" [3]. Her course is also described as "very well organized" with "tons of resources" [3]. In contrast, the other reviews do not provide similar praise for their teaching styles, with Professor Hadar Ziv [4] being described as "chill and reasonable" but with some ambiguous quiz questions, and Professor Michael Shindler [2] not being evaluated in a meaningful way. Therefore, based on the reviews, Professor Jennifer Wong-Ma appears to have the best teaching style. | Relevant          | Accurate          |
| 4   | Which professor at UCI is the most recommended? | Reviews will vary depending on the student                   | Based on the reviews, both Professor Michael Shindler [1] and Professor Jennifer Wong-Ma [3] are highly recommended. Professor Shindler is described as the "goat" and it's stated that "UCI is lucky to have him" [1], while Professor Wong-Ma is considered "one of the best lecturers at UCI" [3]. Additionally, Professor Hadar Ziv [4] is also positively reviewed, with the student stating that he "isn't even that bad of a prof" and that he is "a prof sent from heaven" compared to others. However, Professor Shindler has two reviews [1, 2] that praise him, with one calling him "The Lebron James of UCI professors" [2], which might suggest that he is the most recommended.       | Relevant          | Accurate          |
| 5   | Does Professor Klefstad give weekly quizzes?    | Yes for all his courses                                      | Yes, according to the reviews, Professor Klefstad gives weekly quizzes. This is mentioned in reviews [1] ("one of each every week (quiz in person)") and [4] ("absurdly specific weekly quizzes").                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Relevant          | Accurate          |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:** "What do students think of Klefstad as a professor?"

**What the system returned:** The **top-ranked** retrieved chunk was the review _"The Lebron James of UCI professors. Klefstad is Micheal Jorfraud 😒"_ — correctly about Klefstad — but the system attributed it to **Michael Shindler** and cited Shindler's Rate My Professor page (`/professor/2512998`) instead of Klefstad's (`/professor/17490`). A user who clicks that source lands on the wrong professor's page.

**Root cause (tied to a specific pipeline stage):** This is an **ingestion / metadata** failure, not a retrieval or generation one. In `ingest.py`, every review block in a file inherits the file's professor (the `#` heading) and the file's RMP URL as its `professor` and `source` metadata — i.e. the pipeline assumes _every review on a professor's page is about that professor_. That assumption breaks because RMP reviews routinely name and compare _other_ professors. This particular review was posted on Shindler's page but is entirely about Klefstad, so its stored metadata says "Shindler" while its text says "Klefstad." Retrieval then does its job perfectly — the chunk contains "Klefstad," so it ranks #1 for a Klefstad query — but the attribution metadata riding along with it is wrong, and the generator faithfully repeats that wrong attribution because metadata is the only source-of-truth it's given for who said what. (A secondary contributor surfaced in the same chunk: the emoji was left as the undecoded HTML entity `&#128530;`, showing ingestion also never decoded HTML entities.)

**What you would change to fix it:** The fix belongs in ingestion, where the bad metadata originates. Two levels:

- **Quick mitigation:** decode HTML entities (`html.unescape`) and drop ultra-short, low-content reviews (this joke review is 73 characters and carries almost no signal), which removes the worst offenders.
- **Real fix:** stop treating "page the review was posted on" as "professor the review is about." Either (a) detect when a review's dominantly-named professor differs from the file's professor and relabel or drop it, or (b) reframe the metadata as `posted_on_page: <professor>` and instruct the generation prompt to attribute opinions to the page's professor only when the text doesn't clearly name someone else — so the model can say "a reviewer on Shindler's page joked about Klefstad" instead of misattributing the quote.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**
Writing the spec first meant I had committed to concrete decisions before any code existed — a 350-character chunk size with 100-character overlap, intfloat/e5-base-v2 as the embedding model, top-k=4 retrieval, and the five-stage architecture diagram. When I handed those sections to the AI, the generated chunk.py and embed.py matched my intent on the first pass rather than guessing at parameters I'd have to correct later. The diagram in particular acted as a shared map, so each milestone (ingestion → chunking → embedding → retrieval → generation) was generated as a discrete, wired-together stage instead of one tangled script.

**One way your implementation diverged from the spec, and why:**
My AI Tool Plan for Milestone 3 said I'd build a data_clean.py that scraped the Rate My Professor GraphQL API and converted URLs into structured Markdown automatically. In practice I diverged and prepared the .md review files manually, with the code reading from a local data/ folder instead of fetching anything live. The reason is that RMP is a JavaScript-rendered, Cloudflare-protected site, so a simple fetch wouldn't reliably return reviews and full scraping would have added heavy, brittle dependencies for little benefit at this scale. The secondary divergence was the interface: the spec never named a UI framework, and I settled on Gradio during Milestone 5 because it wires a Python function to a web UI with minimal boilerplate.

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- What I gave the AI: My Milestone 3 plan, where the document sources were Rate My Professor professor URLs, plus my chunking strategy (350-char chunks, 100-char overlap).
- What it produced: An ingest.py that could read several file types (.md, .txt, .pdf) from a local folder and a recursive chunker — but it did not scrape the URLs; it flagged that RMP is JS-rendered/Cloudflare-protected and asked whether to read local files instead of live-scraping.
- What I changed or overrode: I chose the local-file route and did the data collection/cleaning myself, saving one .md file per professor. The AI then rewrote ingest.py to parse my actual file format (splitting on ## Review # headers and capturing class/clarity/helpful/difficulty metadata) instead of the generic loader it first produced.

**Instance 2**

- What I gave the AI: A request to identify a failure case in the pipeline and explain it tied to a specific stage.
- What it produced: It first proposed that "Which professor gives the most homework?" was a failure because the system answered Erik Sudderth instead of my expected Klefstad/Wong-Ma.
- What I changed or overrode: I rejected that — Sudderth was actually a faithful reading of the reviews, so the mismatch was my own prior expectation, not a pipeline bug. I directed it to find a genuine mechanical failure instead, and it surfaced the real one: a review about Klefstad that lives on Shindler's RMP page gets stored with Shindler's professor/URL metadata, so the system cites the wrong professor — a defect in the ingestion stage, not retrieval or generation.

## Query Interface

The interface is a Gradio web app (`app.py`), launched with `python app.py` and opened at `http://127.0.0.1:7860`.

**Input fields:**

- **Your question** — a multi-line textbox where the user types a natural-language question about a UCI CS professor.
- **Ask button** (or pressing Enter) — submits the question to the pipeline.
- **Examples** — five preset questions from the evaluation plan, clickable to populate the box.

**Output fields:**

- **Answer** — the grounded, Groq-generated response with inline [n] citations.
- **Sources** — a list beneath the answer showing each cited chunk's professor, course, relevance score, and a clickable Rate My Professor link.

**Sample interaction transcript:**
User question: Does Professor Klefstad give weekly quizzes?

Answer:
Yes, according to the reviews, Professor Klefstad gives weekly quizzes.
This is mentioned in reviews [1] and [4], with [1] stating "one of each
every week (quiz in person)" and [4] mentioning "absurdly specific weekly
quizzes".

Sources:
[1] Ray Klefstad — 141 (relevance 0.87) — https://www.ratemyprofessors.com/professor/17490
[2] Ray Klefstad — CS141 (relevance 0.86) — https://www.ratemyprofessors.com/professor/17490
[3] Michael Shindler — CS162 (relevance 0.85) — https://www.ratemyprofessors.com/professor/2512998
[4] Ray Klefstad — ICS46 (relevance 0.84) — https://www.ratemyprofessors.com/professor/17490
