import uuid
import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from backend.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Preferences
    optimization_pref = Column(String, default="balanced")  # quality, cost, speed, balanced
    spending_limit = Column(Float, default=100.0)
    preferred_providers = Column(JSON, default=list)  # list of provider IDs
    privacy_mode = Column(String, default="standard")  # strict, standard

    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    credentials = relationship("UserCredential", back_populates="user", cascade="all, delete-orphan")


class Provider(Base):
    __tablename__ = "providers"

    id = Column(String, primary_key=True)  # openai, gemini, anthropic, duckduckgo, pollinations, document_gen
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    website = Column(String, nullable=True)
    icon_url = Column(String, nullable=True)

    tools = relationship("Tool", back_populates="provider_rel")


class Tool(Base):
    __tablename__ = "tools"

    id = Column(String, primary_key=True)  # e.g., openai_gpt4o, gemini_15_pro, duckduckgo_search, pptx_generator
    name = Column(String, nullable=False)
    provider = Column(String, ForeignKey("providers.id"), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String, nullable=False)  # LLM, Research, Image Generation, Document Generation, Coding, etc.
    capabilities = Column(JSON, nullable=False)  # ["text", "reasoning", "multimodal", "search", "pptx"]
    supported_input_types = Column(JSON, nullable=False)  # ["text", "pdf", "image", "json"]
    supported_output_types = Column(JSON, nullable=False)  # ["text", "markdown", "json", "pptx", "pdf", "image"]
    api_endpoint = Column(String, nullable=True)
    auth_config_type = Column(String, default="api_key")  # api_key, none, oauth
    pricing_info = Column(JSON, nullable=True)  # {"input_cost_per_1k": 0.005, "output_cost_per_1k": 0.015}
    speed_rating = Column(Float, default=8.0)  # 1 to 10
    quality_rating = Column(Float, default=9.0)  # 1 to 10
    is_enabled = Column(Boolean, default=True)
    priority = Column(Integer, default=10)
    fallback_priority = Column(Integer, default=5)

    provider_rel = relationship("Provider", back_populates="tools")


class UserCredential(Base):
    __tablename__ = "user_credentials"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    provider_id = Column(String, ForeignKey("providers.id"), nullable=False)
    encrypted_api_key = Column(Text, nullable=False)
    status = Column(String, default="active")  # active, invalid, revoked
    last_tested_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="credentials")


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    original_request = Column(Text, nullable=False)
    status = Column(String, default="created")  # created, in_progress, completed, failed, needs_approval
    output_format = Column(String, default="auto")  # text, markdown, pptx, pdf, docx, code
    budget_limit = Column(Float, default=10.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    owner = relationship("User", back_populates="projects")
    workflows = relationship("Workflow", back_populates="project", cascade="all, delete-orphan")


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    status = Column(String, default="planning")  # planning, executing, completed, failed, requires_approval
    estimated_cost = Column(Float, default=0.0)
    actual_cost = Column(Float, default=0.0)
    requires_user_approval = Column(Boolean, default=False)
    is_user_approved = Column(Boolean, default=False)
    graph_structure = Column(JSON, nullable=True)  # Representation of DAG nodes & edges
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    project = relationship("Project", back_populates="workflows")
    tasks = relationship("Task", back_populates="workflow", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=generate_uuid)
    workflow_id = Column(String, ForeignKey("workflows.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String, nullable=False)  # research, writing, image_gen, pptx_gen, review
    assigned_tool_id = Column(String, ForeignKey("tools.id"), nullable=True)
    status = Column(String, default="pending")  # pending, running, completed, failed, skipped, retrying
    step_order = Column(Integer, default=0)
    dependencies = Column(JSON, default=list)  # list of dependent task IDs
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    tool_selection_reason = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=2)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    workflow = relationship("Workflow", back_populates="tasks")
    executions = relationship("ToolExecution", back_populates="task", cascade="all, delete-orphan")


class ToolExecution(Base):
    __tablename__ = "tool_executions"

    id = Column(String, primary_key=True, default=generate_uuid)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False)
    tool_id = Column(String, ForeignKey("tools.id"), nullable=False)
    status = Column(String, nullable=False)  # success, failure, timeout
    prompt_sent = Column(Text, nullable=True)
    raw_response = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    task = relationship("Task", back_populates="executions")


class Output(Base):
    __tablename__ = "outputs"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    output_type = Column(String, nullable=False)  # text, markdown, pptx, pdf, docx, image, zip
    title = Column(String, nullable=False)
    content = Column(Text, nullable=True)  # text or markdown content
    file_path = Column(String, nullable=True)  # generated file on server
    metadata_info = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, nullable=True)
    action = Column(String, nullable=False)  # e.g., TOOL_EXECUTED, CREDENTIAL_ADDED, PROMPT_INJECTION_BLOCKED
    details = Column(JSON, nullable=True)
    ip_address = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
