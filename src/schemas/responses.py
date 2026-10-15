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

    category: Literal["course", "project", "other"] = Field(description="The category of the student's question.")

    needs_human: bool = Field(description="Whether the question should be handled by a human.")
    evidence_status: Literal["supported", "insufficient"]
    citations: list[int] = Field(default_factory=list, max_length=3)


class AIResponse(BaseModel):
    """Structured response output from the AI service layer."""

    content: str = Field(
        ...,
        description="The generated response text or user-friendly error message.",
    )
    success: bool = Field(
        True,
        description="Flag indicating if the operation succeeded.",
    )
    error_message: str | None = Field(
        None,
        description="Detailed error description if success is False.",
    )
    category: Literal["course", "project", "other"] | None = Field(
        None,
        description="The category of the student's question.",
    )
    needs_human: bool | None = Field(
        None,
        description="Whether the question should be handled by a human.",
    )
    
    model: str | None = None
    evidence_status: Literal["supported", "insufficient"] | None = None
    citations: list[int] = Field(default_factory=list)
    sources: list[dict] = Field(default_factory=list)
    runtime: str | None = None
    endpoint: str | None = None
    elapsed_s: float | None = None
