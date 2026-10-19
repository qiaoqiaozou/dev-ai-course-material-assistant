import gradio as gr
from src.services.ai_service import (
    generate_response,
    INSTALLED_MODELS,
    DEFAULT_MODEL_ID,
)
from src.services.evaluation_service import run_quick_evaluation

def content_to_text(content):
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        return "".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )

    return ""


def history_for_service(history):
    converted = []

    for message in history:
        role = message.get("role")
        text = content_to_text(message.get("content"))

        if role in {"user", "assistant"} and text:
            converted.append({"role": role, "content": text})

    return converted

def format_sources(result):
    if result.evidence_status == "insufficient":
        return "No cited source: the retrieved passages did not contain enough evidence."

    blocks = []

    for number, source in zip(result.citations, result.sources):
        blocks.append(
            f"**[{number}] [{source['title']}]({source['url']})**\n\n"
            f"{source['text']}"
        )

    return "\n\n---\n\n".join(blocks)


def chat_reply(message, history, model_id):
    response = generate_response(
        message,
        history=history_for_service(history),
        model_id = model_id,
    )

    if not response.success:
        return response.content, {"status": "error"},"No sources."

    metadata = {
        "status": "ok",
        "model": response.model,
        "category": response.category,
        "needs_human": response.needs_human,
        "evidence_status": response.evidence_status,
        "citations": response.citations,
        "runtime": response.runtime,
        "endpoint": response.endpoint,
        "elapsed_s": response.elapsed_s,
    }

    return response.content, metadata,format_sources(response)



def build_ui() -> gr.Blocks:
    """
    Constructs the Gradio web interface.

    The UI communicates strictly with `generate_response()`
    in the AI service layer and never directly with Ollama.
    """

    with gr.Blocks(title="AI Course Material Assistant") as demo:

        gr.Markdown(
            """
            # AI Course Material Assistant

            Ask a question about the Development of AI Applications course.

            This assistant helps students understand course information, concepts,
            and project requirements. Always verify important details using the official
            course materials and instructor announcements.
            """
        )

        model_selector = gr.Dropdown(
            choices=INSTALLED_MODELS,
            value=DEFAULT_MODEL_ID,
            label="Model",
        )

        metadata = gr.JSON(label="Validated response")
        sources = gr.Markdown(label="Sources")
        
        gr.ChatInterface(
            fn=chat_reply,
            additional_inputs=[model_selector],
            additional_outputs=[metadata, sources],
        )
        gr.Markdown("## Quick developer evaluation")

        gr.Markdown(
            "Run three fixed cases with the selected model. "
            "Automatic checks do not prove answer correctness. "
            "Review relevance, source quality, correctness, and grounding."
        )

        run_eval = gr.Button("Run quick evaluation")

        results_table = gr.Dataframe(
            headers=[
                "case",
                "question",
                "evidence status",
                "automatic pass",
                "answer",
                "cited evidence",
                "elapsed seconds",
            ],
            interactive=False,
            label="Evaluation results",
        )

        run_eval.click(
            run_quick_evaluation,
            inputs=[model_selector],
            outputs=[results_table],
        )

    return demo
