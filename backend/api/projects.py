from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Project, Workflow, Task, Output
from backend.tool_registry import ToolRegistry

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("")
def list_projects(user_id: str = "default_demo_user", db: Session = Depends(get_db)):
    projects = db.query(Project).filter(Project.user_id == user_id).order_by(Project.created_at.desc()).all()

    results = []
    for p in projects:
        wf = db.query(Workflow).filter(Workflow.project_id == p.id).first()
        results.append({
            "id": p.id,
            "title": p.title,
            "original_request": p.original_request,
            "status": p.status,
            "output_format": p.output_format,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "workflow_id": wf.id if wf else None
        })

    return results


@router.get("/{project_id}")
def get_project_details(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    workflow = db.query(Workflow).filter(Workflow.project_id == project_id).first()
    tasks = []
    if workflow:
        t_records = db.query(Task).filter(Task.workflow_id == workflow.id).order_by(Task.step_order).all()
        for t in t_records:
            tasks.append({
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "category": t.category,
                "assigned_tool_id": t.assigned_tool_id,
                "tool_selection_reason": t.tool_selection_reason,
                "status": t.status,
                "step_order": t.step_order,
                "dependencies": t.dependencies,
                "output_data": t.output_data
            })

    outputs = db.query(Output).filter(Output.project_id == project_id).all()
    output_list = []
    for o in outputs:
        output_list.append({
            "id": o.id,
            "output_type": o.output_type,
            "title": o.title,
            "content": o.content,
            "file_path": o.file_path,
            "metadata_info": o.metadata_info
        })

    return {
        "project": {
            "id": project.id,
            "title": project.title,
            "original_request": project.original_request,
            "status": project.status,
            "output_format": project.output_format,
            "budget_limit": project.budget_limit,
            "created_at": project.created_at.isoformat() if project.created_at else None
        },
        "workflow": {
            "id": workflow.id if workflow else None,
            "status": workflow.status if workflow else None,
            "estimated_cost": workflow.estimated_cost if workflow else 0.0,
            "actual_cost": workflow.actual_cost if workflow else 0.0,
            "graph_structure": workflow.graph_structure if workflow else None
        },
        "tasks": tasks,
        "outputs": output_list
    }
