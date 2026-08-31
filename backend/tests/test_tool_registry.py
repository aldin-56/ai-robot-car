import pytest
import os
import uuid
from backend.database import Base, engine, SessionLocal
from backend.models import User, UserCredential, Project, Workflow, Task, Tool
from backend.security import encrypt_api_key
from backend.tool_registry import ToolRegistry


def test_tool_registry_seeding_and_selection():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    registry = ToolRegistry(db)

    # Check seeded tools
    tools = db.query(Tool).all()
    assert len(tools) >= 5

    # Create test user
    uid = str(uuid.uuid4())[:8]
    user = User(email=f"registry_{uid}@litemind.ai", username=f"reguser_{uid}", hashed_password="pw")
    db.add(user)
    db.commit()

    # Add Gemini credentials using env var or test string
    test_key = os.getenv("GEMINI_API_KEY", "test_gemini_api_key_123")
    cred = UserCredential(
        user_id=user.id,
        provider_id="gemini",
        encrypted_api_key=encrypt_api_key(test_key)
    )
    db.add(cred)
    db.commit()

    # Test tool selection for text reasoning capability
    selected_llm = registry.select_best_tool("text", user.id, optimization_pref="best_quality")
    assert selected_llm is not None
    assert selected_llm["provider"] == "gemini"
    assert "Gemini" in selected_llm["tool_name"]

    # Test tool selection for search capability (public provider DuckDuckGo)
    selected_search = registry.select_best_tool("search", user.id)
    assert selected_search is not None
    assert selected_search["provider"] == "duckduckgo"

    # Test tool selection for PPTX presentation generation
    selected_pptx = registry.select_best_tool("pptx", user.id)
    assert selected_pptx is not None
    assert selected_pptx["tool_id"] == "pptx_generator"

    # Cleanup
    db.delete(cred)
    db.delete(user)
    db.commit()
    db.close()
    print("Tool Registry unit tests passed successfully!")


if __name__ == "__main__":
    test_tool_registry_seeding_and_selection()
