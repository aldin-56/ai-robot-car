import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from litemind.database.seed import seed_tools
from litemind.database.db import init_db
from litemind.api.routes import router

# Seed tool database on startup
init_db()
seed_tools()

app = FastAPI(
    title="LiteMind AI Orchestration Platform",
    description="Multi-AI Goal Orchestrator Engine",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

# Mount exported files directory
os.makedirs("exports", exist_ok=True)
app.mount("/exports", StaticFiles(directory="exports"), name="exports")

# Mount Static Frontend
os.makedirs("litemind/static", exist_ok=True)
app.mount("/", StaticFiles(directory="litemind/static", html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("litemind.main:app", host="0.0.0.0", port=8000, reload=True)
