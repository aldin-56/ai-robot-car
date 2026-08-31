import pytest
from backend.database import Base, engine, SessionLocal
from backend.models import User, UserCredential
from backend.security import encrypt_api_key
from backend.orchestrator.planner import WorkflowPlanner


def test_workflow_planner_pptx():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    user = User(email="planner_test@litemind.ai", username="planneruser", hashed_password="pw")
    db.add(user)
    db.commit()

    planner = WorkflowPlanner(db, user.id)

    # Test PPTX planning request
    plan = planner.plan_workflow(
        request_text="Create a presentation about renewable energy for Class 9.",
        output_format="auto"
    )

    assert plan["output_format"] == "pptx"
    assert "graph_structure" in plan
    nodes = plan["graph_structure"]["nodes"]
    assert len(nodes) >= 3

    # Check capabilities in DAG
    capabilities = [n["required_capability"] for n in nodes]
    assert "search" in capabilities or "text" in capabilities
    assert "presentation_generation" in capabilities or "text" in capabilities

    # Cleanup
    db.delete(user)
    db.commit()
    db.close()
    print("Workflow Planner unit test passed successfully!")


if __name__ == "__main__":
    test_workflow_planner_pptx()
