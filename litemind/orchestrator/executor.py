import time
import json
import logging
from typing import Dict, Any, List, Optional, Callable
from sqlalchemy.orm import Session

from litemind.database.models import Project, Workflow, Task, ToolExecution, UserSettings
from litemind.registry.service import ToolRegistry
from litemind.orchestrator.security import PromptSecurity
from litemind.services.export_service import ExportService

logger = logging.getLogger("litemind.executor")


class WorkflowExecutor:
    """
    DAG Execution Engine.
    Executes tasks according to topological dependencies, passes outputs between steps,
    selects appropriate tools, handles retries and fallback providers on failure,
    and runs quality control checks.
    """

    def __init__(
        self,
        db: Session,
        workflow_id: str,
        user_id: str,
        event_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        self.db = db
        self.workflow_id = workflow_id
        self.user_id = user_id
        self.event_callback = event_callback or (lambda evt: None)

        self.workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not self.workflow:
            raise ValueError(f"Workflow {workflow_id} not found.")

        self.project = db.query(Project).filter(Project.id == self.workflow.project_id).first()
        self.settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()

    def _emit(self, event_type: str, task_id: Optional[str], data: Dict[str, Any]):
        evt = {
            "workflow_id": self.workflow_id,
            "project_id": self.project.id if self.project else None,
            "event_type": event_type,  # workflow_start, task_start, task_complete, task_fallback, task_failed, workflow_complete
            "task_id": task_id,
            "timestamp": time.time(),
            "data": data
        }
        try:
            self.event_callback(evt)
        except Exception as e:
            logger.error(f"Error emitting event: {e}")

    def execute_workflow(self) -> Dict[str, Any]:
        """Execute all tasks in the DAG in dependency order."""
        self.workflow.status = "running"
        self.project.status = "executing"
        self.db.commit()

        self._emit("workflow_start", None, {
            "status": "running",
            "message": "Starting workflow execution engine...",
            "request": self.project.original_request
        })

        db_tasks = self.db.query(Task).filter(Task.workflow_id == self.workflow_id).all()
        task_map = {t.id: t for t in db_tasks}
        completed_outputs: Dict[str, Any] = {}

        total_cost = 0.0

        # Execute loop until all tasks completed or fatal failure
        while True:
            pending_tasks = [t for t in task_map.values() if t.status == "pending"]
            if not pending_tasks:
                break

            # Find tasks whose dependencies are satisfied
            ready_tasks = []
            for task in pending_tasks:
                deps = task.dependencies or []
                all_deps_satisfied = all(
                    dep_id in task_map and task_map[dep_id].status == "completed"
                    for dep_id in deps
                )
                if all_deps_satisfied:
                    ready_tasks.append(task)

            if not ready_tasks:
                # Deadlock or broken dependency graph
                failed_tasks = [t for t in task_map.values() if t.status == "failed"]
                if failed_tasks:
                    self.workflow.status = "failed"
                    self.project.status = "failed"
                    self.db.commit()
                    self._emit("workflow_failed", None, {"error": "Dependencies blocked due to prior task failure."})
                    return {"success": False, "error": "Workflow failed due to task dependency failure."}
                break

            # Execute ready tasks (sequential or parallel-ready)
            for task in ready_tasks:
                success, task_out, task_cost = self._execute_single_task(task, completed_outputs)
                total_cost += task_cost

                if not success:
                    # Task failed after fallback attempts
                    self.workflow.status = "failed"
                    self.project.status = "failed"
                    self.db.commit()
                    self._emit("workflow_failed", task.id, {
                        "error": f"Task '{task.task_name}' failed: {task.error_message}"
                    })
                    return {"success": False, "error": task.error_message}

                completed_outputs[task.id] = task_out

        # Final Workflow Consolidation & File Exporting
        final_artifacts = ExportService.compile_project_artifacts(
            project_title=self.project.title,
            output_type=self.project.output_type,
            task_outputs=completed_outputs
        )

        self.workflow.status = "completed"
        self.project.status = "completed"
        self.project.total_cost = total_cost
        self.project.artifacts = final_artifacts
        self.project.final_output = {
            "summary": f"Successfully generated {self.project.output_type} with {len(completed_outputs)} task outputs.",
            "artifacts": final_artifacts,
            "task_results": completed_outputs
        }
        self.db.commit()

        self._emit("workflow_complete", None, {
            "status": "completed",
            "total_cost": total_cost,
            "artifacts": final_artifacts,
            "final_output": self.project.final_output
        })

        return {
            "success": True,
            "project_id": self.project.id,
            "workflow_id": self.workflow_id,
            "total_cost": total_cost,
            "artifacts": final_artifacts
        }

    def _execute_single_task(
        self,
        task: Task,
        dependency_outputs: Dict[str, Any]
    ) -> tuple[bool, Any, float]:
        """
        Execute an individual task with intelligent tool selection, prompt injection protection,
        output passing, retries, and fallback tool selection.
        """
        task.status = "in_progress"
        self.db.commit()

        # Collect upstream outputs from dependencies
        upstream_context = []
        for dep_id in (task.dependencies or []):
            if dep_id in dependency_outputs:
                upstream_context.append(f"Output from step [{dep_id}]:\n{json.dumps(dependency_outputs[dep_id])}")

        combined_context_str = "\n\n".join(upstream_context)

        # Build prompt safely with Prompt Injection Protection
        safe_prompt = PromptSecurity.wrap_task_prompt(
            system_instruction=f"Task Category: {task.category}. Execute the following objective cleanly.",
            user_goal=task.input_data.get("prompt", task.task_name) if task.input_data else task.task_name,
            untrusted_context=combined_context_str
        )

        excluded_tools = []
        task_cost = 0.0

        # Attempt execution with retries and fallback tools
        for attempt in range(1, 3):
            # Select best connected tool
            selection = ToolRegistry.select_best_tool(
                db=self.db,
                user_id=self.user_id,
                category=task.category,
                required_capability=task.input_data.get("required_capability", "text") if task.input_data else "text",
                settings=self.settings,
                exclude_tool_ids=excluded_tools
            )

            if not selection:
                error_msg = f"No connected or enabled tool available for category '{task.category}'. Please connect a supported AI provider in Tool Settings."
                task.status = "failed"
                task.error_message = error_msg
                self.db.commit()
                return False, None, 0.0

            selected_tool = selection["tool"]
            adapter = selection["adapter"]
            api_key = selection["api_key"]
            reason = selection["reason"]

            task.tool_id = selected_tool.id
            task.tool_selection_reason = reason
            self.db.commit()

            self._emit("task_start", task.id, {
                "task_name": task.task_name,
                "tool_id": selected_tool.id,
                "tool_name": selected_tool.name,
                "tool_reason": reason,
                "category": task.category
            })

            payload = {
                "prompt": safe_prompt,
                "model_id": selected_tool.id,
                "task_category": task.category,
                "capabilities": selected_tool.capabilities,
                "json_mode": True if task.category in ("LLM", "Research", "Quality Control") else False,
                "goal": self.project.original_request,
                "outputs": dependency_outputs
            }

            start_time = time.time()
            res = adapter.execute(payload, api_key=api_key)
            latency = time.time() - start_time

            cost = res.get("cost", 0.0)
            task_cost += cost

            # Record Tool Execution Log
            exec_log = ToolExecution(
                task_id=task.id,
                tool_id=selected_tool.id,
                status="success" if res["success"] else "failed",
                request_payload={"tool_id": selected_tool.id, "attempt": attempt},
                response_payload=res.get("data") if res["success"] else {"error": res.get("error")},
                latency_seconds=latency,
                cost=cost
            )
            self.db.add(exec_log)
            self.db.commit()

            if res["success"]:
                task.status = "completed"
                task.output_data = res["data"]
                task.execution_time_seconds = latency
                task.cost = cost
                self.db.commit()

                self._emit("task_complete", task.id, {
                    "task_name": task.task_name,
                    "tool_name": selected_tool.name,
                    "execution_time": round(latency, 2),
                    "cost": cost,
                    "output": res["data"]
                })
                return True, res["data"], task_cost

            else:
                # Primary tool failed -> log fallback warning and try alternative tool
                logger.warning(f"Task '{task.task_name}' failed with {selected_tool.id}: {res.get('error')}. Attempting fallback...")
                excluded_tools.append(selected_tool.id)

                self._emit("task_fallback", task.id, {
                    "task_name": task.task_name,
                    "failed_tool": selected_tool.name,
                    "error": res.get("error"),
                    "message": "Selected provider failed or returned an error. Looking for another suitable connected tool..."
                })

        # All retries / fallbacks exhausted
        task.status = "failed"
        task.error_message = f"Failed after trying alternative tools: {res.get('error')}"
        self.db.commit()
        return False, None, task_cost
