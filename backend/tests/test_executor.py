import pytest
import os
import uuid
from backend.database import Base, engine, SessionLocal
from backend.models import User, UserCredential, Project, Workflow, Task
from backend.security import encrypt_api_key
from backend.orchestrator.planner import WorkflowPlanner
from backend.orchestrator.executor import WorkflowExecutor


def test_workflow_execution():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    uid = str(uuid.uuid4())[:8]
    user = User(email=f"executor_{uid}@litemind.ai", username=f"execuser_{uid}", hashed_password="pw")
    db.add(user)
    db.commit()

    test_key = os.getenv("GEMINI_API_KEY", "test_gemini_api_key_123")
    cred = UserCredential(
        user_id=user.id,
        provider_id="gemini",
        encrypted_api_key=encrypt_api_key(test_key)
    )
    db.add(cred)
    db.commit()

    project = Project(
        user_id=user.id,
        title="Test Executive Presentation Project",
        original_request="Create a 3 slide presentation about AI Orchestration.",
        output_format="pptx"
    )
    db.add(project)
    db.commit()

    planner = WorkflowPlanner(db, user.id)
    plan = planner.plan_workflow(project.original_request, output_format="pptx")

    workflow = Workflow(
        project_id=project.id,
        status="planned",
        estimated_cost=plan["estimated_cost"],
        graph_structure=plan["graph_structure"]
    )
    db.add(workflow)
    db.commit()

    for node in plan["graph_structure"]["nodes"]:
        t = Task(
            workflow_id=workflow.id,
            title=node["title"],
            description=node["description"],
            category=node["required_capability"],
            assigned_tool_id=node["assigned_tool_id"],
            tool_selection_reason=node["tool_selection_reason"],
            step_order=node["step_order"],
            dependencies=node["depends_on_indices"],
            status="pending"
        )
        db.add(t)
    db.commit()

    events = []
    def progress_handler(evt):
        events.append(evt)

    executor = WorkflowExecutor(db, user.id, progress_callback=progress_handler)
    exec_result = executor.execute_workflow(workflow.id)

    assert exec_result["success"] is True
    assert len(events) >= len(plan["graph_structure"]["nodes"])
    assert exec_result["final_output"]["output_id"] is not None

    db.close()
    print("Workflow Executor unit test passed successfully!")


if __name__ == "__main__":
    test_workflow_execution()
