from unittest.mock import patch, MagicMock
from backend.adapters.llm_adapter import LLMAdapter


def test_llm_adapter_validation():
    adapter = LLMAdapter("openai", "gpt-4o-mini", api_key="sk-test")
    assert adapter.validate_input({"prompt": "Hello world"}) is True
    assert adapter.validate_input({"prompt": ""}) is False
    assert adapter.validate_input({}) is False


def test_llm_adapter_no_key_execution():
    adapter = LLMAdapter("openai", "gpt-4o-mini", api_key=None)
    result = adapter.execute("LLM", {"prompt": "Hello"})
    assert result["success"] is False
    assert "not connected" in result["error"].lower() or "missing" in result["error"].lower()


@patch("requests.post")
def test_openai_llm_execution(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "This is a test AI response."}}]
    }
    mock_post.return_value = mock_response

    adapter = LLMAdapter("openai", "gpt-4o-mini", api_key="sk-valid-key")
    result = adapter.execute("LLM", {"prompt": "Tell me a story"})

    assert result["success"] is True
    assert result["output"]["content"] == "This is a test AI response."
    assert result["execution_time_ms"] >= 0


if __name__ == "__main__":
    test_llm_adapter_validation()
    test_llm_adapter_no_key_execution()
    print("LLM Adapter unit tests passed successfully!")
