import gradio as gr
from src.services.ai_service import (
    generate_response,
    INSTALLED_MODELS,
    DEFAULT_MODEL_ID,
)


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


def chat_reply(message, history, model_id):
    response = generate_response(
        message,
        history_for_service(history),
        model_id = model_id,
    )

    if not response.success:
        return response.content, {"status": "error"}

    return response.content, {
        "category": response.category,
        "needs_human": response.needs_human,
    }




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
        
        gr.ChatInterface(
            fn=chat_reply,
            additional_inputs=[model_selector],
            additional_outputs=[metadata],
        )

    return demo
