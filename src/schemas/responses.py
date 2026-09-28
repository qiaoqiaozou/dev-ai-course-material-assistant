from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class UserRequest(BaseModel):
    """Minimal schema for validating incoming user input."""

    message: str = Field(..., description="The user's prompt or message.")


class CourseResponse(BaseModel):
    """Structured response expected from the AI model."""

    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        str_strip_whitespace=True,
    )

    answer: str = Field(
        min_length=1,
        max_length=600,
        description="The answer to the student's question.",
    )

    category: Literal["course", "project", "other"] = Field(
        description="The category of the student's question."
    )

    needs_human: bool = Field(
        description="Whether the question should be handled by a human."
    )


class AIResponse(BaseModel):
    """Minimal schema for structured response output from the AI service layer."""

    content: str = Field(..., description="The generated response text or user-friendly error message.")
    success: bool = Field(True, description="Flag indicating if the operation succeeded.")
    error_message: str | None = Field(None, description="Detailed error description if success is False.")
