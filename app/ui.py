import gradio as gr
from src.services.ai_service import generate_response


def build_ui() -> gr.Blocks:
    """
    Constructs the Gradio web interface.
    
    Architectural Principle: The UI communicates strictly with `generate_response()`
    in the AI service layer and never directly with Ollama or the model client.
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

        with gr.Row():
            user_input = gr.Textbox(
                lines=3,
                placeholder="Ask a question about the course...",
                label="Course Question",
            )

        submit_btn = gr.Button("Send", variant="primary")

        with gr.Row():
            output_box = gr.Textbox(
                lines=8,
                label="Assistant Response",
                interactive=False,
            )

        # Connect UI actions exclusively to the service layer function
        submit_btn.click(
            fn=generate_response,
            inputs=user_input,
            outputs=output_box,
        )
        user_input.submit(
            fn=generate_response,
            inputs=user_input,
            outputs=output_box,
        )

    return demo
