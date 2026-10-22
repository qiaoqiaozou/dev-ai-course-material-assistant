# Project decisions

Use this decision log to document significant technical and architectural choices made by your team during development.

## Decision 1 — Model selection

**Decision:**
Use local models through Ollama and allow users to select an installed model.

**Alternatives considered:**
We tried Llama and Qwen models.
We evaluated `qwen3:8b` and `qwen3.5:2b` with the same three questions.

**Why we chose this:**
Local Ollama models do not need a cloud API key.
The model dropdown lets us compare models without changing the main workflow.
In our small evaluation, `qwen3:8b` gave more complete answers.
`qwen3.5:2b` was faster but missed one required item.

---

## Decision 2 — Additional AI capability

**Decision:**
Add RAG using course webpages, Sentence Transformers, and Chroma.

**Why it is needed:**
The model needs course-specific information.
RAG supplies evidence and lets students inspect the sources.

**Alternatives considered:**
Using only the model's own knowledge would not provide reliable course sources.
Sending all course pages with every question would create a much larger request.
We retrieve text chunks for most questions.
For questions matching "sample project" or "sample projects",
we use the full loaded page because chunk retrieval missed some project names.

---

## Decision 3 — Architecture

**Decision:**
Keep the UI, AI service, RAG code, model client, and schemas separate.
Run the application locally with Gradio and Ollama

**Why:**
The UI does not need to manage model calls or citation checks.
The same AI service supports both chat and the evaluation button.
This keeps the application simple and easier to test.

The Chroma index stays in memory and is rebuilt at startup.
This avoids a separate database setup, but startup needs network access
and takes time.
