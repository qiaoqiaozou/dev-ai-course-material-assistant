import gradio as gr
from src.services.ai_service import generate_response


def chat_with_history(
    user_message: str,
    model_history: list[dict],
):
    """
    Sends the user's message together with previous conversation history
    to the AI service, then updates the model history and chatbot display.
    """

    if not user_message or not user_message.strip():
        return "", model_history, []

    user_message = user_message.strip()

    # Send the previous conversation history to the AI service.
    response = generate_response(
        user_message,
        history=model_history,
    )


    # Update the history used by the model.
    new_history = model_history + [
        {
            "role": "user",
            "content": user_message,
        },
        {
            "role": "assistant",
            "content": response,
        },
    ]

    # Create a separate copy for the Chatbot display.
    chatbot_display = [
        {
            "role": message["role"],
            "content": message["content"],
        }
        for message in new_history
    ]

    return "", new_history, chatbot_display


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

        chatbot = gr.Chatbot(
            label="Conversation",
            value=[],
        )

        # Stores only the conversation history sent to the model.
        model_history = gr.State([])

        with gr.Row():

            user_input = gr.Textbox(
                lines=3,
                placeholder="Ask a question about the course...",
                label="Course Question",
            )

        submit_btn = gr.Button(
            "Send",
            variant="primary",
        )

        submit_btn.click(
            fn=chat_with_history,
            inputs=[
                user_input,
                model_history,
            ],
            outputs=[
                user_input,
                model_history,
                chatbot,
            ],
        )

        user_input.submit(
            fn=chat_with_history,
            inputs=[
                user_input,
                model_history,
            ],
            outputs=[
                user_input,
                model_history,
                chatbot,
            ],
        )

    return demo
