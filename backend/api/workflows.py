import os
import json
import asyncio
import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from backend.database import get_db, SessionLocal
from backend.models import Project, Workflow, Task, Output, AuditLog
from backend.orchestrator.planner import WorkflowPlanner
from backend.orchestrator.executor import WorkflowExecutor

router = APIRouter(prefix="/api/workflows", tags=["workflows"])

# In-memory queue store for SSE streaming listeners
event_queues = {}

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


class SubmitTaskSchema(BaseModel):
    user_id: str = "default_demo_user"
    request_text: str
    output_format: str = "auto"
    budget_limit: float = 10.0
    optimization_pref: str = "balanced"


@router.post("/submit")
def submit_new_task(data: SubmitTaskSchema, db: Session = Depends(get_db)):
    # 1. Create Project
    project = Project(
        user_id=data.user_id,
        title=data.request_text[:60],
        original_request=data.request_text,
        status="created",
        output_format=data.output_format,
        budget_limit=data.budget_limit
    )
    db.add(project)
    db.commit()

    # 2. Generate Plan with Orchestrator Planner
    planner = WorkflowPlanner(db, data.user_id)
    plan = planner.plan_workflow(
        request_text=data.request_text,
        output_format=data.output_format,
        budget_limit=data.budget_limit,
        optimization_pref=data.optimization_pref
    )

    # 3. Save Workflow
    workflow = Workflow(
        project_id=project.id,
        status="requires_user_approval" if plan["requires_user_approval"] else "planned",
        estimated_cost=plan["estimated_cost"],
        requires_user_approval=plan["requires_user_approval"],
        graph_structure=plan["graph_structure"]
    )
    db.add(workflow)
    db.commit()

    # 4. Save Task Nodes
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

    # Audit log entry
    audit = AuditLog(
        user_id=data.user_id,
        action="WORKFLOW_PLANNED",
        details={"project_id": project.id, "workflow_id": workflow.id, "request": data.request_text}
    )
    db.add(audit)
    db.commit()

    return {
        "project_id": project.id,
        "workflow_id": workflow.id,
        "requires_approval": plan["requires_user_approval"],
        "estimated_cost": plan["estimated_cost"],
        "graph_structure": plan["graph_structure"]
    }


def run_background_execution(workflow_id: str, user_id: str):
    """Executes workflow using its own independent database session."""
    db = SessionLocal()
    try:
        def sync_callback(evt):
            q = event_queues.get(workflow_id)
            if q:
                try:
                    q.put_nowait(evt)
                except Exception:
                    pass

        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if workflow:
            workflow.status = "executing"
            if workflow.project:
                workflow.project.status = "in_progress"
            db.commit()

        executor = WorkflowExecutor(db, user_id, progress_callback=sync_callback)
        res = executor.execute_workflow(workflow_id)

        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if workflow and res.get("success") and workflow.project:
            workflow.project.status = "completed"
            db.commit()

    finally:
        db.close()


@router.post("/{workflow_id}/execute")
def trigger_workflow_execution(workflow_id: str, background_tasks: BackgroundTasks, user_id: str = "default_demo_user", db: Session = Depends(get_db)):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found.")

    workflow.status = "executing"
    if workflow.project:
        workflow.project.status = "in_progress"
    db.commit()

    # Pass background execution with independent DB session management
    background_tasks.add_task(run_background_execution, workflow_id, user_id)

    return {"message": "Execution started", "workflow_id": workflow_id}


@router.get("/{workflow_id}/stream")
async def stream_workflow_progress(workflow_id: str):
    """Server-Sent Events (SSE) streaming endpoint for live workflow status."""

    q = asyncio.Queue()
    event_queues[workflow_id] = q

    async def event_generator():
        try:
            yield f"data: {json.dumps({'event': 'connected', 'workflow_id': workflow_id})}\n\n"
            while True:
                evt = await asyncio.wait_for(q.get(), timeout=30.0)
                yield f"data: {json.dumps(evt)}\n\n"
                if evt.get("status") in ["completed", "failed"] and evt.get("task_id") is None:
                    break
        except asyncio.TimeoutError:
            yield f"data: {json.dumps({'event': 'ping'})}\n\n"
        finally:
            if workflow_id in event_queues:
                del event_queues[workflow_id]

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """File upload handler for PDFs, DOCX, PPTX, CSV, TXT, Images."""
    file_location = os.path.join(UPLOAD_DIR, f"{int(datetime.datetime.utcnow().timestamp())}_{file.filename}")
    with open(file_location, "wb") as f:
        content = await file.read()
        f.write(content)

    return {
        "filename": file.filename,
        "file_path": file_location,
        "size_bytes": len(content)
    }


@router.get("/download")
def download_generated_file(path: str):
    """Download handler for generated PPTX, PDF, or DOCX files."""
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Requested file does not exist.")
    return FileResponse(path)
