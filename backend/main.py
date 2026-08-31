import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.database import Base, engine, SessionLocal
from backend.tool_registry import ToolRegistry

from backend.api.auth import router as auth_router
from backend.api.credentials import router as cred_router
from backend.api.projects import router as proj_router
from backend.api.tools import router as tool_router
from backend.api.workflows import router as workflow_router

# Initialize database tables
Base.metadata.create_all(bind=engine)

# Seed default tool registry
db = SessionLocal()
try:
    ToolRegistry(db)
finally:
    db.close()

app = FastAPI(
    title="LiteMind AI Orchestration Platform API",
    description="Full-stack AI orchestration engine powering goal-based multi-tool workflows.",
    version="1.0.0"
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router)
app.include_router(cred_router)
app.include_router(proj_router)
app.include_router(tool_router)
app.include_router(workflow_router)

# Serve generated outputs statically
os.makedirs("generated_outputs", exist_ok=True)
app.mount("/outputs", StaticFiles(directory="generated_outputs"), name="outputs")


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app": "LiteMind AI Orchestrator",
        "version": "1.0.0"
    }
