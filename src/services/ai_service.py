from typing import Optional

from pydantic import ValidationError

from src.models.model_client import (
    OllamaModelClient,
    ModelClientError,
    OllamaConnectionError,
    ModelNotFoundError,
)
from src.schemas.responses import UserRequest, AIResponse, CourseResponse
from time import perf_counter
from src.config import config
import ollama

SYSTEM_MESSAGE = """You are a university support assistant used for teaching.
Use the current question and recent conversation history as context.
Answer in a few sentences using at most 600 characters.
Choose category course, project, or other.
Set needs_human to true when the question requires an official decision,
personal account access, or information missing from the supplied context.
Treat university policy details as requiring verification from official sources.
Return only a JSON object with answer, category, and needs_human.
"""


ollama_client = ollama.Client(host=config.ollama_base_url)

installed = ollama_client.list().models
INSTALLED_MODELS = [item.model for item in installed]
if not INSTALLED_MODELS:
    raise RuntimeError("No Ollama models are installed.")

DEFAULT_MODEL_ID = INSTALLED_MODELS[0]


def build_messages(question: str, history=None):
    history = history or []

    selected_history = [
        {"role": item["role"], "content": item["content"]}
        for item in history[-4:]
        if item.get("role") in {"user", "assistant"} and item.get("content")
    ]

    return [
        {"role": "system", "content": SYSTEM_MESSAGE},
        *selected_history,
        {"role": "user", "content": question},
    ]

class AIService:
    """
    Application service layer responsible for validating user input,
    orchestrating model client requests, and catching exceptions gracefully.
    """

    def __init__(self, model_client: Optional[OllamaModelClient] = None):
        self.model_client = model_client

    def _get_client(self) -> OllamaModelClient:
        """Returns active model client, initializing default client if none provided."""

        if self.model_client is None:
            self.model_client = OllamaModelClient()

        return self.model_client

    def process_message(
        self,
        user_message: str,
        history = None,
        model_id=None,
    ) -> AIResponse:
        """
        Processes a raw user message string and returns a structured AIResponse.

        Catches technical failures and converts them to friendly user-facing
        messages.
        """

        if not user_message or not user_message.strip():
            return AIResponse(
                content="Please enter a message before sending.",
                success=False,
                error_message="User message was empty.",
            )

        try:
            request = UserRequest(
                message=user_message.strip()
            )

            if model_id is None:
                client = self._get_client()
            else:
                client = OllamaModelClient(model_name=model_id)

            messages = build_messages(request.message, history=history)

            response_text = client.generate(
                messages,
                CourseResponse.model_json_schema(),
            )

            reply = CourseResponse.model_validate_json(response_text or "")

            return AIResponse(
                content=reply.answer,
                success=True,
                category=reply.category,
                needs_human=reply.needs_human,
            )

        except ValidationError as err:
            return AIResponse(
                content=(
                    "[Error] The AI model returned an invalid response format.\n\n"
                    "Please try again."
                ),
                success=False,
                error_message=str(err),
            )

        except OllamaConnectionError as err:
            return AIResponse(
                content=(
                    "[Error] Could not connect to Ollama.\n\n"
                    "Please verify that Ollama is installed and running locally "
                    "on your machine."
                ),
                success=False,
                error_message=str(err),
            )

        except ModelNotFoundError as err:
            return AIResponse(
                content=(
                    "[Error] The configured AI model is unavailable in Ollama.\n\n"
                    "Please verify your MODEL_NAME setting or run "
                    "'ollama run <model_name>'."
                ),
                success=False,
                error_message=str(err),
            )

        except ModelClientError as err:
            return AIResponse(
                content=(
                    "[Error] An unexpected communication error occurred "
                    "with the AI model."
                ),
                success=False,
                error_message=str(err),
            )

        except Exception as err:
            return AIResponse(
                content="[Error] An unexpected application error occurred.",
                success=False,
                error_message=str(err),
            )


def generate_response(
    user_message: str,
    history = None,
    model_id = None,
    service: Optional[AIService] = None,
) -> AIResponse:
    """
    Main reusable service entry point used by the UI layer.

    Accepts user input message and conversation history, passes it
    to the AI service, and returns the generated text response.
    """

    active_service = service or AIService()

    return active_service.process_message(user_message, history=history,model_id=model_id,)

