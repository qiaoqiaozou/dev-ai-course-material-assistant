# AI Course Material Assistant

A RAG-based question-answering application that helps students find and understand information from the course website.

## Team members

- Qiaoqiao Zou (qiaoqiao.zou@student.hamk.fi)
- Xiaomeng Du (xiaomeng23000@student.hamk.fi)
- Neupane Nitish Raj (email@example.com)

## Problem

### Intended users
Students

### Problem statement
The course information is distributed across multiple webpages and chapters. Students may need to search through several pages to find a specific requirement, deadline, definition, or explanation. This takes time and can lead to misunderstandings when relevant information appears on different pages.

### Why AI is appropriate
When a student asks a complex question, the system can integrate information from multiple sources, and the language model can then clearly explain the retrieved information. RAG (Retrieval-Augmented Generation) technology enables the application to answer questions using selected course materials rather than relying solely on the model's internal knowledge, resulting in more accurate answers.

AI does not rely solely on hard-coded rules written by programmers; instead, it understands natural language and generates responses. While it is difficult for traditional programs to write rules covering every possible way of expression, language models can comprehend the underlying semantics.

## Solution

The application provides a Gradio interface where students can ask questions about a course.
The system retrieves relevant passages from selected course webpages. It sends the question and retrieved passages to a local model through Ollama, validates the model response.
If the course materials do not contain enough information, the application will state that it could not find a supported answer.

## Main user workflow

1. **User Input:** The user submits a prompt or query via the Gradio user interface.
2. **Processing & Guardrails:** The application service layer (`src/services/ai_service.py`) validates and formats the request.
3. **Model Response:** The model client calls Ollama locally and returns the response back through the service layer to the UI.

## Architecture

Below is the initial starter architecture. As your project evolves with additional capabilities, replace or extend this diagram in [`docs/architecture.md`](docs/architecture.md).

```text
User
  ↓
Gradio UI (app/ui.py)
  ↓
Application / AI Service (src/services/ai_service.py)
  ↓
Model Client (src/models/model_client.py)
  ↓
Ollama (Local LLM Server)
```

> **Core Architectural Rule:** The user interface must NEVER communicate directly with the model client or Ollama. All interactions must pass through the service layer (`ai_service.py`).

## Model

- **Model used:** `llama3.2` 
- **Selection rationale:** We hope that selected model is supported by the provided starter setup, can run locally in our teamembers' laptops, and is suitable for creating the initial prototype. The final model choice may change after testing response quality and hardware requirements.

## Additional AI capability

Select at least one additional capability to implement for your final project:

- [x] RAG (Retrieval-Augmented Generation)
- [ ] Tools / External API integration
- [ ] Model Context Protocol (MCP)
- [ ] Agentic workflow (Model-selected actions based on observations)
- [ ] Memory / Persistent state
- [ ] Multimodal interaction (Text + Images)
- [ ] Other: ______________________

### Capability justification
RAG is necessary because the application must answer questions using the current course materials rather than relying only on the model's internal knowledge. Without incorporating RAG, the answers provided might be overly broad or lack accuracy.

## Setup

### 1. Create the Conda environment

```bash
conda env create -f environment.yml
```

### 2. Activate the environment

```bash
conda activate dev-ai-project
```

### 3. Configure environment variables

Copy `.env.example` to create your local `.env` configuration file:

On Linux / macOS:
```bash
cp .env.example .env
```

On Windows (Command Prompt / PowerShell):
```powershell
copy .env.example .env
```

Ensure `.env` contains valid values for `OLLAMA_BASE_URL` and `MODEL_NAME`:
```env
OLLAMA_BASE_URL=http://localhost:11434
MODEL_NAME=llama3.2
```

### 4. Start Ollama

Make sure Ollama is installed and running locally, then pull your configured model:

```bash
ollama run llama3.2
```

### 5. Run the application

Run the application from the root directory of the project:

```bash
python -m app.main
```

Then open your browser at `http://localhost:7860`.

### 6. Run automated tests

```bash
pytest
```

## Evaluation

The evaluation will consider relatived question, out-of-scope questions, and empty or invalid input.

Starter test cases can be found in [`evaluation/test_cases.json`](evaluation/test_cases.json).

Refer to [`evaluation/README.md`](evaluation/README.md) for guidelines on defining success, edge cases, and failure scenarios.

## Known limitations

- The first version will support only selected public pages from the Development of AI Applications course(our course).

- The application will not access course content requiring authentication.

- The initial version may not process information contained only in PDF slides, images, diagrams, or videos.

- Answer quality will depend on retrieval quality and the selected local model

## Future improvements

- Supports loading more complex web pages.
- supporting PDF slides and other document formats.
