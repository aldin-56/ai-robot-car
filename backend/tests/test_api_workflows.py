import pytest
import time
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_workflow_submission_and_execution():
    # 1. Health check
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

    # 2. Submit new task
    submit_res = client.post("/api/workflows/submit", json={
        "user_id": "default_demo_user",
        "request_text": "Create a report on sustainable energy trends.",
        "output_format": "pdf",
        "budget_limit": 10.0
    })
    assert submit_res.status_code == 200
    data = submit_res.json()
    assert "project_id" in data
    assert "workflow_id" in data
    wf_id = data["workflow_id"]

    # 3. Trigger execution
    exec_res = client.post(f"/api/workflows/{wf_id}/execute")
    assert exec_res.status_code == 200

    print("Workflow submission & execution API tests passed successfully!")


if __name__ == "__main__":
    test_workflow_submission_and_execution()
