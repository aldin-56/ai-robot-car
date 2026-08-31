import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.database import Base, engine
from backend.api.auth import router as auth_router
from backend.api.credentials import router as cred_router
from backend.api.projects import router as proj_router
from backend.api.tools import router as tool_router

test_app = FastAPI()
test_app.include_router(auth_router)
test_app.include_router(cred_router)
test_app.include_router(proj_router)
test_app.include_router(tool_router)

client = TestClient(test_app)


def test_api_crud_routes():
    Base.metadata.create_all(bind=engine)

    # Auth Register Test
    res = client.post("/api/auth/register", json={
        "email": "testcrud@litemind.ai",
        "username": "testcruduser",
        "password": "password123"
    })
    assert res.status_code == 200 or res.status_code == 400

    # Tools list test
    res = client.get("/api/tools")
    assert res.status_code == 200
    assert len(res.json()) >= 4

    # Credentials list test
    res = client.get("/api/credentials")
    assert res.status_code == 200

    print("API CRUD route tests passed successfully!")


if __name__ == "__main__":
    test_api_crud_routes()
