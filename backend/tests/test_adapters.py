import pytest
import os
from unittest.mock import patch, MagicMock
from backend.adapters.search_adapter import SearchAdapter
from backend.adapters.document_adapter import DocumentAdapter
from backend.adapters.image_adapter import ImageAdapter


def test_search_adapter():
    adapter = SearchAdapter()
    assert adapter.authenticate() is True
    assert adapter.validate_input({"query": "renewable energy"}) is True
    assert adapter.validate_input({}) is False


@patch("duckduckgo_search.DDGS.text")
def test_search_adapter_execution(mock_ddg):
    mock_ddg.return_value = [
        {"title": "Renewable Energy Overview", "body": "Solar and wind are key.", "href": "https://example.com/solar"}
    ]
    adapter = SearchAdapter()
    result = adapter.execute("search", {"query": "renewable energy", "scrape_webpages": False})

    assert result["success"] is True
    assert len(result["output"]["results"]) == 1
    assert result["output"]["results"][0]["title"] == "Renewable Energy Overview"


def test_document_adapter_pptx():
    adapter = DocumentAdapter()
    input_data = {
        "format": "pptx",
        "title": "Test Presentation",
        "slides": [
            {"title": "Intro", "bullets": ["Point 1", "Point 2"]}
        ]
    }
    result = adapter.execute("pptx_gen", input_data)
    assert result["success"] is True
    assert result["output"]["file_path"].endswith(".pptx")
    assert os.path.exists(result["output"]["file_path"])


def test_document_adapter_pdf():
    adapter = DocumentAdapter()
    input_data = {
        "format": "pdf",
        "title": "Test PDF Document",
        "content": "This is a test PDF paragraph."
    }
    result = adapter.execute("pdf_gen", input_data)
    assert result["success"] is True
    assert result["output"]["file_path"].endswith(".pdf")
    assert os.path.exists(result["output"]["file_path"])


def test_image_adapter_pollinations():
    adapter = ImageAdapter(provider_id="pollinations")
    result = adapter.execute("image_gen", {"prompt": "a cute cat on a hill"})
    assert result["success"] is True
    assert "pollinations.ai" in result["output"]["image_url"]


if __name__ == "__main__":
    test_search_adapter()
    test_document_adapter_pptx()
    test_document_adapter_pdf()
    test_image_adapter_pollinations()
    print("All search, document, and image adapter tests passed successfully!")
