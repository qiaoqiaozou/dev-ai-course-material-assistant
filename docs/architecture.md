# Architecture Documentation

This document explains how the AI Course Material Assistant works.
The application uses the starter project's layered structure and adds RAG.

## Application Architecture

The application follows the starter project's layered structure.
RAG gets course evidence before the model generates an answer.

At startup, the app extracts webpage text and keeps it in DOCUMENTS.
It also splits the text into chunks, creates embeddings, and stores them
in an in-memory Chroma index.

For each question, the app gets evidence, sends it with the question
to the selected local model, checks the response, and displays the result.

![Application architecture](images/architecture.png)

Validation checks the response format and citation rules.
It does not guarantee answer correctness.

### Two ways to get evidence

For most questions, the app turns the question into a query embedding.
It then searches Chroma for up to three relevant text chunks.

In our tests, this search did not find all three sample projects.
It often found the page introduction and only one project name.

To avoid missing projects, questions with "sample project" or
"sample projects" use the full text of the Sample Projects page.
The app extracts and loads this text at startup.
This path does not use vector search.

The app also splits this page into chunks and adds them to Chroma.
It keeps the full text in DOCUMENTS for the special path above.

Both paths return evidence to the same AI service.
The service sends the evidence to the selected local model through
the model client and Ollama.
It then checks the response format and citation rules.

The special rule matches these English phrases without checking letter case.
Other wording may not use this path.



### Core Design Rules

1. **Strict UI Isolation:** The Gradio user interface (`app/ui.py`) MUST NOT directly instantiate `OllamaModelClient` or make direct API calls to Ollama. It delegates chat requests to `generate_response()` in `src/services/ai_service.py`. The evaluation button calls run_quick_evaluation() in evaluation_service.py, which uses the same AI service.
2. **Controlled Failure Handling:** The model client handles low-level runtime exceptions (e.g., connection errors or missing models). The service layer converts technical exceptions into structured, user-understandable responses. Startup errors may stop the application before the UI opens.
3. **Data Schemas:** Request inputs and response structures are validated using Pydantic models in `src/schemas/responses.py`. `UserRequest` defines the input,
   `CourseResponse` defines the model reply, and `AIResponse`
   defines the result sent to the UI.
4. **Citation Checks:** A supported answer must have citations.
   An insufficient-evidence answer must not have citations.
   Each citation number must refer to a supplied evidence passage.
   These rules do not prove that the answer is correct or complete.

---

## Implemented AI Capability: RAG

RAG helps the application answer questions using course webpages
instead of relying only on the model's own knowledge.

### Web Documents

`src/capabilities/web_documents.py` reads the course sitemap.
It loads documentation pages under the same course website path.

Each document keeps its title, URL, course label ("DEV-AI"), and extracted text.
The loader does not read external websites or linked PDFs, images,
videos, and notebooks.

### Chunking and Indexing

`src/capabilities/rag.py` groups the extracted text into chunks.
The target length is 120 words. Text blocks are added whole,
so a chunk can be longer.

If the final block has fewer than 40 words, it is joined to the
previous chunk when one exists. Each chunk also includes the page title.

Sentence Transformers creates embeddings.
Chroma stores the chunks, embeddings, and source information in memory.
The app rebuilds the index when it starts.

### Retrieval and Answer Generation

For most questions, the app first turns the question into a query embedding.
It uses this vector to search Chroma for up to three relevant text chunks.

Questions with an English exercise number, such as "Exercise 3",
search only the matching exercise page.

If the question contains "sample project" or "sample projects",
and the Sample Projects page is available in DOCUMENTS,
the app returns its full text.
It does not create a query embedding or search Chroma.

The AI service combines the evidence, question, instructions,
and recent chat history. The model client sends the request to
the selected local model through Ollama.

The service checks the reply format and citation rules.
The UI then displays the answer, cited text, source links,
and runtime information.

### Conversation History

The UI sends chat history to the service.
The service takes the last four messages and keeps valid user
and assistant messages for the model request.


### Evaluation

The Run quick evaluation button runs three fixed questions
with the selected model. Each question uses empty chat history.

The result table shows answers, cited evidence, processing time,
and simple automatic checks.

We also read the answers and sources by hand.
Test cases and results are recorded in the `evaluation/` folder.
Automated application tests are in `tests/test_ai_service.py`.
