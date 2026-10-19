from unittest.mock import MagicMock, patch
import pytest

from src.config import config
from src.models.model_client import (
    ModelClientError,
    OllamaConnectionError,
    ModelNotFoundError,
)
from src.services.ai_service import AIService, generate_response


def test_config_loading():
    """Verify that configuration settings load expected string values from environment or defaults."""
    assert config.ollama_base_url is not None
    assert config.model_name is not None
    assert isinstance(config.ollama_base_url, str)
    assert isinstance(config.model_name, str)


def test_empty_input_validation():
    """Verify that empty or whitespace inputs are rejected gracefully without invoking the model."""
    mock_client = MagicMock()
    service = AIService(model_client=mock_client)

    # Test empty string
    response_empty = service.process_message("")
    assert response_empty.success is False
    assert "Please enter a message" in response_empty.content
    assert mock_client.generate.call_count == 0

    # Test whitespace string
    response_spaces = service.process_message("   ")
    assert response_spaces.success is False
    assert mock_client.generate.call_count == 0


def test_successful_response_generation():
    """Verify that valid input invokes model client and returns the generated string response."""
    mock_client = MagicMock()
    mock_client.model_name = "test-model"
    mock_client.generate.return_value = (
        '{"answer": "Hello! I am an AI assistant.", '
        '"category": "other", '
        '"needs_human": false,'
        '"evidence_status": "supported", '
        '"citations": [1]}'
    )

    evidence = [
        {
            "id": "test-chunk-1",
            "text": "The workshop uses an energy dataset.",
            "title": "Test course guide",
            "url": "https://example.com/course",
        }
    ]

    service = AIService(model_client=mock_client)

    with patch(
        "src.services.ai_service.retrieve",
        return_value=evidence,
    ):
        result = generate_response("Hello, AI", service=service)

    assert result.content == "Hello! I am an AI assistant."
    assert result.success is True
    assert result.category == "other"
    assert result.needs_human is False
   


def test_ollama_connection_error_handling():
    """Verify that Ollama connection failures produce a friendly application-level error message."""
    mock_client = MagicMock()
    mock_client.generate.side_effect = OllamaConnectionError("Connection refused at http://localhost:11434")
    service = AIService(model_client=mock_client)

    response = service.process_message("Test message")

    assert response.success is False
    assert "Could not connect to Ollama" in response.content
    assert "Connection refused" in response.error_message


def test_model_not_found_error_handling():
    """Verify that missing model exceptions are converted into controlled user messages."""
    mock_client = MagicMock()
    mock_client.generate.side_effect = ModelNotFoundError("Model llama3.2 not found locally")
    service = AIService(model_client=mock_client)

    response = service.process_message("Test message")

    assert response.success is False
    assert "configured AI model is unavailable" in response.content
    assert "llama3.2 not found" in response.error_message

def test_supported_response_requires_citations():
    """Verify that a supported answer without citations is rejected."""
    mock_client = MagicMock()
    mock_client.model_name = "test-model"
    mock_client.generate.return_value = (
        '{"answer": "The workshop uses an energy dataset.", '
        '"category": "course", '
        '"needs_human": false, '
        '"evidence_status": "supported", '
        '"citations": []}'
    )

    evidence = [
        {
            "id": "test-chunk-1",
            "text": "The workshop uses an energy dataset.",
            "title": "Test course guide",
            "url": "https://example.com/course",
        }
    ]

    service = AIService(model_client=mock_client)

    with patch(
        "src.services.ai_service.retrieve",
        return_value=evidence,
    ):
        result = generate_response(
            "What dataset does the workshop use?",
            service=service,
        )

    assert result.success is False
    assert result.error_message == "Supported answer has no citations."
    assert result.sources == []


def test_insufficient_response_rejects_citations():
    """Verify that an insufficient answer with citations is rejected."""
    mock_client = MagicMock()
    mock_client.model_name = "test-model"
    mock_client.generate.return_value = (
        '{"answer": "The supplied documents do not contain enough information.", '
        '"category": "other", '
        '"needs_human": true, '
        '"evidence_status": "insufficient", '
        '"citations": [1]}'
    )

    evidence = [
        {
            "id": "test-chunk-1",
            "text": "The workshop uses an energy dataset.",
            "title": "Test course guide",
            "url": "https://example.com/course",
        }
    ]

    service = AIService(model_client=mock_client)

    with patch(
        "src.services.ai_service.retrieve",
        return_value=evidence,
    ):
        result = generate_response(
            "What is today's cafeteria menu?",
            service=service,
        )

    assert result.success is False
    assert result.error_message == "Insufficient answer includes citations."
    assert result.sources == []