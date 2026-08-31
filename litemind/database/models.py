import datetime
import uuid
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from litemind.database.db import Base


def generate_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    connections = relationship("UserConnection", back_populates="user", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")


class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    optimization_preference = Column(String, default="balanced")  # quality, cost, speed, balanced
    max_workflow_budget = Column(Float, default=10.0)  # in USD
    max_tool_calls = Column(Integer, default=20)
    preferred_providers = Column(JSON, default=list)  # ["openai", "anthropic", "gemini"]
    privacy_external_data = Column(Boolean, default=True)  # allow external content passing
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="settings")


class Tool(Base):
    __tablename__ = "tools"

    id = Column(String, primary_key=True)  # e.g. "openai-gpt4o", "gemini-1.5-pro", "duckduckgo-search"
    name = Column(String, nullable=False)
    provider = Column(String, nullable=False)  # openai, google, anthropic, duckduckgo, python_pptx, reportlab
    description = Column(Text, nullable=False)
    category = Column(String, nullable=False)  # LLM, Research, Image Generation, Coding, Presentation, Document, etc.
    capabilities = Column(JSON, nullable=False)  # ["text", "reasoning", "multimodal", "code", "search"]
    supported_input_types = Column(JSON, nullable=False)  # ["text", "pdf", "image", "json"]
    supported_output_types = Column(JSON, nullable=False)  # ["text", "json", "image", "pptx", "pdf", "docx"]
    api_endpoint = Column(String, nullable=True)
    pricing_info = Column(JSON, nullable=True)  # {"prompt_token": 0.000005, "completion_token": 0.000015}
    speed_rating = Column(Float, default=8.0)  # 1-10
    quality_rating = Column(Float, default=9.0)  # 1-10
    enabled = Column(Boolean, default=True)
    priority = Column(Integer, default=1)
    fallback_priority = Column(Integer, default=2)

    executability_requires_auth = Column(Boolean, default=True)  # False for local generators (python-pptx, reportlab)

    executions = relationship("ToolExecution", back_populates="tool")


class UserConnection(Base):
    __tablename__ = "user_connections"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    provider = Column(String, nullable=False)  # openai, gemini, anthropic, stability, tavily
    encrypted_api_key = Column(Text, nullable=False)
    status = Column(String, default="connected")  # connected, invalid, error
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="connections")


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    original_request = Column(Text, nullable=False)
    output_type = Column(String, default="presentation")  # presentation, document, code, text, report
    status = Column(String, default="pending")  # pending, executing, waiting_approval, completed, failed
    final_output = Column(JSON, nullable=True)
    artifacts = Column(JSON, default=list)  # paths/URLs to generated files (.pptx, .pdf, .docx, .zip)
    total_cost = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="projects")
    workflows = relationship("Workflow", back_populates="project", cascade="all, delete-orphan")


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    status = Column(String, default="planned")  # planned, running, paused, completed, failed
    execution_plan = Column(JSON, nullable=False)  # Task graph structure
    quality_score = Column(Float, nullable=True)
    quality_review = Column(JSON, nullable=True)  # Review results
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    project = relationship("Project", back_populates="workflows")
    tasks = relationship("Task", back_populates="workflow", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=generate_uuid)
    workflow_id = Column(String, ForeignKey("workflows.id"), nullable=False)
    task_name = Column(String, nullable=False)  # e.g., "Research Climate Change", "Write Content"
    category = Column(String, nullable=False)  # Research, LLM, Image, Presentation, Document, Quality
    status = Column(String, default="pending")  # pending, in_progress, completed, failed, skipped
    tool_id = Column(String, ForeignKey("tools.id"), nullable=True)
    tool_selection_reason = Column(Text, nullable=True)  # "Why this tool?" explanation
    dependencies = Column(JSON, default=list)  # List of prerequisite task IDs
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    execution_time_seconds = Column(Float, nullable=True)
    cost = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    workflow = relationship("Workflow", back_populates="tasks")
    tool_executions = relationship("ToolExecution", back_populates="task", cascade="all, delete-orphan")


class ToolExecution(Base):
    __tablename__ = "tool_executions"

    id = Column(String, primary_key=True, default=generate_uuid)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False)
    tool_id = Column(String, ForeignKey("tools.id"), nullable=False)
    status = Column(String, default="success")  # success, failed
    request_payload = Column(JSON, nullable=True)
    response_payload = Column(JSON, nullable=True)
    latency_seconds = Column(Float, nullable=True)
    cost = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    task = relationship("Task", back_populates="tool_executions")
    tool = relationship("Tool", back_populates="executions")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, nullable=True)
    action = Column(String, nullable=False)  # e.g., "USER_CONNECT_TOOL", "WORKFLOW_EXECUTE"
    details = Column(JSON, nullable=True)
    ip_address = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
