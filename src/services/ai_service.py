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
from src.capabilities.rag import retrieve


SYSTEM_MESSAGE = """You are a university support assistant used for teaching.
Answer the user's question using only the supplied evidence.
Give a complete, direct answer to the question.
When asked which projects are listed, name all projects listed in the supplied evidence.
Do not return only an introductory phrase.
Do not invent facts that are missing from the evidence.

If the evidence supports the answer:
- set evidence_status to supported;
- cite only the relevant evidence numbers shown in square brackets;
- citation numbers identify supplied evidence passages, not items listed inside them;
- if only evidence [1] is supplied, the only valid citation number is 1;
- several facts or projects from the same passage share the same citation number.

If the evidence does not contain enough information:
- say that the supplied documents do not contain enough information;
- set evidence_status to insufficient;
- return an empty citations list;
- set needs_human to true.

Choose the category based on the user's question:
- course: course concepts, chapters, exercises, teaching sample projects, schedule, software setup, and learning resources;
- project: the student's final group project, including its requirements, implementation, submission, assessment, and presentation;
- other: unrelated questions or questions whose topic cannot be determined.

Exercises and teaching sample projects belong to course.
Classify the topic independently of whether sufficient evidence was retrieved.

Teaching sample projects belong to course, not project.
Numbered course exercises belong to exercise, not project.
Classify the topic independently of whether sufficient evidence was retrieved.

Return only the structured response requested by the schema.
"""


ollama_client = ollama.Client(host=config.ollama_base_url)

installed = ollama_client.list().models
INSTALLED_MODELS = [item.model for item in installed]
if not INSTALLED_MODELS:
    raise RuntimeError("No Ollama models are installed.")

DEFAULT_MODEL_ID = INSTALLED_MODELS[0]


def build_grounded_messages(question: str, evidence, history=None):
    history = history or []

    selected_history = [
        {"role": item["role"], "content": item["content"]}
        for item in history[-4:]
        if item.get("role") in {"user", "assistant"} and item.get("content")
    ]

    evidence_text = "\n\n".join(
        f"[{number}] {item['text']}"
        for number, item in enumerate(evidence, start=1)
    )

    return [
        {"role": "system", "content": SYSTEM_MESSAGE},
        *selected_history,
        {"role": "user", 
         "content": (
                f"Question: {question}\n\n"
                f"Evidence:\n{evidence_text}\n\n"
                f"Allowed citation numbers: "
                f"{list(range(1, len(evidence) + 1))}\n"
                "Use only these numbers in citations. "
                "Do not use the numbering of projects or items "
                "inside an evidence passage."
            ),
        },

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

        if model_id is not None and model_id not in INSTALLED_MODELS:
            return AIResponse(
                content=f"Model {model_id!r} is not installed.",
                success=False,
                model=model_id,
            )

        started = perf_counter()
        try:
            request = UserRequest(
                message=user_message.strip()
            )
            evidence = retrieve(
                request.message,
                course="DEV-AI",
                top_k=3,
            )

            if model_id is None:
                client = self._get_client()
            else:
                client = OllamaModelClient(model_name=model_id)

            messages = build_grounded_messages(request.message, evidence, history=history)

            response_text = client.generate(
                messages,
                CourseResponse.model_json_schema(),
            )


            reply = CourseResponse.model_validate_json(response_text or "")

            if reply.evidence_status == "supported" and not reply.citations:
                return AIResponse(
                    content=(
                        "The model reported a supported answer "
                        "without source references. Please try again."
                    ),
                    success=False,
                    error_message="Supported answer has no citations.",
                )

            if reply.evidence_status == "insufficient" and reply.citations:
                return AIResponse(
                    content=(
                        "The model reported insufficient evidence "
                        "but included source references. Please try again."
                    ),
                    success=False,
                    error_message="Insufficient answer includes citations.",
                )

            if any(
                number < 1 or number > len(evidence)
                for number in reply.citations
            ):
                return AIResponse(
                    content="The model returned an invalid source reference.",
                    success=False,
                    error_message="Invalid source reference.",
                )


            sources = [
                evidence[number - 1]
                for number in reply.citations
            ]

            return AIResponse(
                content=reply.answer,
                success=True,
                category=reply.category,
                needs_human=reply.needs_human,
                model=client.model_name,
                evidence_status=reply.evidence_status,
                citations=reply.citations,
                sources=sources,
                runtime="Ollama",
                endpoint=config.ollama_base_url,
                elapsed_s=round(perf_counter() - started, 2),
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
    service: Optional[AIService] = None,
     *,
    history=None,
    model_id=None,
) -> AIResponse:
    """
    Main reusable service entry point used by the UI layer.

    Accepts user input message and conversation history, passes it
    to the AI service, and returns the generated text response.
    """

    active_service = service or AIService()

    return active_service.process_message(user_message, history=history,model_id=model_id,)

