from typing import Optional

from pydantic import ValidationError

from src.models.model_client import (
    OllamaModelClient,
    ModelClientError,
    OllamaConnectionError,
    ModelNotFoundError,
)
from src.schemas.responses import UserRequest, AIResponse, CourseResponse


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
        history: Optional[list[dict]] = None,
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

            response_text = self._get_client().generate(
                request.message,
                response_format=CourseResponse.model_json_schema(),
                history=history,
            )

            reply = CourseResponse.model_validate_json(
                response_text
            )

            # Protect the UI from a rare model formatting mistake where
            # an extra closing brace is included at the end of the answer.
            answer = reply.answer

            if answer.endswith("}"):
                answer = answer[:-1].rstrip()

            return AIResponse(
                content=answer,
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
    history: Optional[list[dict]] = None,
    service: Optional[AIService] = None,
) -> str:
    """
    Main reusable service entry point used by the UI layer.

    Accepts user input message and conversation history, passes it
    to the AI service, and returns the generated text response.
    """

    active_service = service or AIService()

    response = active_service.process_message(
        user_message,
        history=history,
    )

    return response.content
