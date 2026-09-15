import asyncio
import json
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session

from litemind.database.db import get_db
from litemind.database.models import User, UserConnection, UserSettings, Project, Workflow, Task, Tool
from litemind.database.security import encrypt_secret, decrypt_secret
from litemind.registry.service import ToolRegistry
from litemind.orchestrator.planner import WorkflowPlanner
from litemind.orchestrator.executor import WorkflowExecutor
from litemind.services.file_processor import FileProcessor

router = APIRouter(prefix="/api")

# Event queues per workflow for SSE streaming
WORKFLOW_QUEUES: Dict[str, List[asyncio.Queue]] = {}


def get_default_user(db: Session) -> User:
    """Helper to retrieve or create default active user session for LiteMind."""
    user = db.query(User).filter(User.email == "user@litemind.ai").first()
    if not user:
        user = User(id="default-user-id", email="user@litemind.ai", hashed_password="hashed_demo_password", full_name="LiteMind User")
        db.add(user)
        # Create default user settings
        settings = UserSettings(user_id=user.id)
        db.add(settings)
        db.commit()
        db.refresh(user)
    return user


@router.get("/tools")
def get_tools(db: Session = Depends(get_db)):
    """Return all tools in Tool Registry enriched with connection state."""
    user = get_default_user(db)
    return ToolRegistry.list_tools_for_user(db, user.id)


@router.get("/connections")
def get_connections(db: Session = Depends(get_db)):
    """Return list of connected providers for the current user."""
    user = get_default_user(db)
    connections = db.query(UserConnection).filter(UserConnection.user_id == user.id).all()
    return [
        {
            "id": c.id,
            "provider": c.provider,
            "status": c.status,
            "enabled": c.enabled,
            "created_at": c.created_at.isoformat()
        }
        for c in connections
    ]


@router.post("/connections")
def save_connection(
    payload: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Connect or update an API key for an AI provider securely.
    Encrypts API key before saving to database.
    """
    user = get_default_user(db)
    provider = payload.get("provider")
    api_key = payload.get("api_key")

    if not provider or not api_key:
        raise HTTPException(status_code=400, detail="Provider and API key are required.")

    adapter = ToolRegistry.get_adapter(provider)
    if adapter:
        is_valid = adapter.authenticate(api_key)
        status = "connected" if is_valid else "invalid"
    else:
        status = "connected"

    existing = db.query(UserConnection).filter(
        UserConnection.user_id == user.id,
        UserConnection.provider == provider
    ).first()

    enc_key = encrypt_secret(api_key)

    if existing:
        existing.encrypted_api_key = enc_key
        existing.status = status
        existing.enabled = True
    else:
        conn = UserConnection(
            user_id=user.id,
            provider=provider,
            encrypted_api_key=enc_key,
            status=status,
            enabled=True
        )
        db.add(conn)

    db.commit()
    return {"message": f"Successfully updated connection for {provider}.", "status": status}


@router.post("/connections/test")
def test_connection(payload: Dict[str, Any]):
    """Test validity of a provider API key without storing."""
    provider = payload.get("provider")
    api_key = payload.get("api_key")

    adapter = ToolRegistry.get_adapter(provider)
    if not adapter:
        return {"valid": True, "message": "Local integration ready."}

    valid = adapter.authenticate(api_key)
    return {
        "valid": valid,
        "message": f"Connection to {provider} {'successful ✓' if valid else 'failed. Check API key credentials.'}"
    }


@router.get("/settings")
def get_user_settings(db: Session = Depends(get_db)):
    user = get_default_user(db)
    settings = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
    if not settings:
        settings = UserSettings(user_id=user.id)
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return {
        "optimization_preference": settings.optimization_preference,
        "max_workflow_budget": settings.max_workflow_budget,
        "max_tool_calls": settings.max_tool_calls,
        "preferred_providers": settings.preferred_providers or [],
        "privacy_external_data": settings.privacy_external_data
    }


@router.post("/settings")
def update_user_settings(payload: Dict[str, Any], db: Session = Depends(get_db)):
    user = get_default_user(db)
    settings = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
    if not settings:
        settings = UserSettings(user_id=user.id)
        db.add(settings)

    settings.optimization_preference = payload.get("optimization_preference", settings.optimization_preference)
    settings.max_workflow_budget = float(payload.get("max_workflow_budget", settings.max_workflow_budget))
    settings.max_tool_calls = int(payload.get("max_tool_calls", settings.max_tool_calls))
    settings.preferred_providers = payload.get("preferred_providers", settings.preferred_providers)
    settings.privacy_external_data = bool(payload.get("privacy_external_data", settings.privacy_external_data))

    db.commit()
    return {"message": "Settings updated successfully."}


@router.get("/projects")
def list_projects(db: Session = Depends(get_db)):
    user = get_default_user(db)
    projects = db.query(Project).filter(Project.user_id == user.id).order_by(Project.created_at.desc()).all()
    return [
        {
            "id": p.id,
            "title": p.title,
            "original_request": p.original_request,
            "output_type": p.output_type,
            "status": p.status,
            "total_cost": p.total_cost,
            "created_at": p.created_at.isoformat(),
            "artifacts_count": len(p.artifacts or [])
        }
        for p in projects
    ]


@router.get("/projects/{project_id}")
def get_project_details(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    workflows = db.query(Workflow).filter(Workflow.project_id == project_id).all()
    wf_data = []
    for wf in workflows:
        tasks = db.query(Task).filter(Task.workflow_id == wf.id).all()
        wf_data.append({
            "id": wf.id,
            "status": wf.status,
            "tasks": [
                {
                    "id": t.id,
                    "task_name": t.task_name,
                    "category": t.category,
                    "status": t.status,
                    "tool_id": t.tool_id,
                    "tool_selection_reason": t.tool_selection_reason,
                    "dependencies": t.dependencies,
                    "output_data": t.output_data,
                    "execution_time_seconds": t.execution_time_seconds,
                    "cost": t.cost,
                    "error_message": t.error_message
                }
                for t in tasks
            ]
        })

    return {
        "id": project.id,
        "title": project.title,
        "original_request": project.original_request,
        "output_type": project.output_type,
        "status": project.status,
        "final_output": project.final_output,
        "artifacts": project.artifacts or [],
        "total_cost": project.total_cost,
        "created_at": project.created_at.isoformat(),
        "workflows": wf_data
    }


@router.post("/projects/create")
async def create_project_and_workflow(
    request_text: str = Form(...),
    output_type: str = Form("presentation"),
    file: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    """
    Accept user request, parse optional file attachment, generate dynamic task DAG,
    and initialize project and workflow records.
    """
    user = get_default_user(db)

    file_context = ""
    if file:
        content = await file.read()
        extracted = FileProcessor.extract_text_from_file(file.filename, content)
        file_context = extracted["extracted_text"]

    # Plan workflow DAG dynamically
    plan = WorkflowPlanner.analyze_goal_and_plan(
        user_request=request_text,
        output_type=output_type,
        file_context=file_context
    )

    project = Project(
        user_id=user.id,
        title=plan["title"],
        original_request=request_text,
        output_type=plan["output_type"],
        status="pending"
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    workflow = Workflow(
        project_id=project.id,
        status="planned",
        execution_plan=plan
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)

    # Insert task records
    for t_data in plan["tasks"]:
        inp = {"prompt": t_data["input_prompt"], "required_capability": t_data["required_capability"]}
        if file_context:
            inp["file_context"] = file_context

        task_record = Task(
            id=t_data["id"],
            workflow_id=workflow.id,
            task_name=t_data["task_name"],
            category=t_data["category"],
            status="pending",
            dependencies=t_data["dependencies"],
            input_data=inp
        )
        db.add(task_record)

    db.commit()

    return {
        "project_id": project.id,
        "workflow_id": workflow.id,
        "title": project.title,
        "output_type": project.output_type,
        "tasks_count": len(plan["tasks"])
    }


@router.post("/workflows/{workflow_id}/execute")
def trigger_workflow_execution(workflow_id: str, db: Session = Depends(get_db)):
    """Trigger background execution of the workflow graph."""
    wf = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found.")

    user = get_default_user(db)

    def event_listener(evt):
        if workflow_id in WORKFLOW_QUEUES:
            for q in WORKFLOW_QUEUES[workflow_id]:
                q.put_nowait(evt)

    executor = WorkflowExecutor(db, workflow_id, user.id, event_callback=event_listener)
    result = executor.execute_workflow()

    return result


@router.get("/workflows/{workflow_id}/stream")
async def stream_workflow_progress(workflow_id: str):
    """
    Server-Sent Events (SSE) endpoint to stream real-time workflow DAG execution progress.
    """
    q: asyncio.Queue = asyncio.Queue()
    if workflow_id not in WORKFLOW_QUEUES:
        WORKFLOW_QUEUES[workflow_id] = []
    WORKFLOW_QUEUES[workflow_id].append(q)

    async def event_generator():
        try:
            while True:
                # Wait for next event
                evt = await q.get()
                yield f"data: {json.dumps(evt)}\n\n"
                if evt.get("event_type") in ("workflow_complete", "workflow_failed"):
                    break
        except asyncio.CancelledError:
            pass
        finally:
            if workflow_id in WORKFLOW_QUEUES and q in WORKFLOW_QUEUES[workflow_id]:
                WORKFLOW_QUEUES[workflow_id].remove(q)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
