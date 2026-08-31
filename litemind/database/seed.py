from litemind.database.db import SessionLocal, init_db
from litemind.database.models import Tool

INITIAL_TOOLS = [
    {
        "id": "litemind-local-llm",
        "name": "LiteMind Built-in Reasoning Engine",
        "provider": "local_llm",
        "description": "High-speed local orchestration LLM for fallback reasoning, structured document planning, and code synthesis.",
        "category": "LLM",
        "capabilities": ["text", "reasoning", "coding", "analysis"],
        "supported_input_types": ["text", "json"],
        "supported_output_types": ["text", "json", "code"],
        "api_endpoint": None,
        "pricing_info": {"prompt_per_1k": 0.00, "completion_per_1k": 0.00},
        "speed_rating": 10.0,
        "quality_rating": 8.5,
        "enabled": True,
        "priority": 3,
        "fallback_priority": 1,
        "executability_requires_auth": False
    },
    {
        "id": "openai-gpt4o",
        "name": "OpenAI GPT-4o",
        "provider": "openai",
        "description": "State-of-the-art multimodal flagship model for complex reasoning, writing, coding, and structured output.",
        "category": "LLM",
        "capabilities": ["text", "reasoning", "coding", "multimodal", "analysis"],
        "supported_input_types": ["text", "pdf", "image", "json"],
        "supported_output_types": ["text", "json", "code"],
        "api_endpoint": "https://api.openai.com/v1/chat/completions",
        "pricing_info": {"prompt_per_1k": 0.0025, "completion_per_1k": 0.010},
        "speed_rating": 8.5,
        "quality_rating": 9.8,
        "enabled": True,
        "priority": 1,
        "fallback_priority": 2,
        "executability_requires_auth": True
    },
    {
        "id": "openai-gpt4o-mini",
        "name": "OpenAI GPT-4o Mini",
        "provider": "openai",
        "description": "Fast and lightweight model ideal for quick text generation, formatting, and high-efficiency subtasks.",
        "category": "LLM",
        "capabilities": ["text", "reasoning", "coding"],
        "supported_input_types": ["text", "json"],
        "supported_output_types": ["text", "json"],
        "api_endpoint": "https://api.openai.com/v1/chat/completions",
        "pricing_info": {"prompt_per_1k": 0.00015, "completion_per_1k": 0.0006},
        "speed_rating": 9.5,
        "quality_rating": 8.5,
        "enabled": True,
        "priority": 2,
        "fallback_priority": 1,
        "executability_requires_auth": True
    },
    {
        "id": "gemini-1.5-pro",
        "name": "Google Gemini 1.5 Pro",
        "provider": "gemini",
        "description": "Next-gen multimodal model with massive 1M token context window and strong research/synthesis capabilities.",
        "category": "LLM",
        "capabilities": ["text", "reasoning", "multimodal", "analysis"],
        "supported_input_types": ["text", "pdf", "image", "json"],
        "supported_output_types": ["text", "json"],
        "api_endpoint": "https://generativelanguage.googleapis.com/v1beta",
        "pricing_info": {"prompt_per_1k": 0.00125, "completion_per_1k": 0.005},
        "speed_rating": 8.0,
        "quality_rating": 9.5,
        "enabled": True,
        "priority": 1,
        "fallback_priority": 2,
        "executability_requires_auth": True
    },
    {
        "id": "anthropic-claude-3-5-sonnet",
        "name": "Anthropic Claude 3.5 Sonnet",
        "provider": "anthropic",
        "description": "Industry leader in coding, deep reasoning, structured writing, and visual parsing.",
        "category": "LLM",
        "capabilities": ["text", "reasoning", "coding", "multimodal"],
        "supported_input_types": ["text", "pdf", "image"],
        "supported_output_types": ["text", "json", "code"],
        "api_endpoint": "https://api.anthropic.com/v1/messages",
        "pricing_info": {"prompt_per_1k": 0.003, "completion_per_1k": 0.015},
        "speed_rating": 8.8,
        "quality_rating": 9.9,
        "enabled": True,
        "priority": 1,
        "fallback_priority": 2,
        "executability_requires_auth": True
    },
    {
        "id": "web-research-engine",
        "name": "LiteMind Web & Fact Research Engine",
        "provider": "web_research",
        "description": "Real-time web search and content extraction service to gather live facts, statistics, and domain information.",
        "category": "Research",
        "capabilities": ["web_search", "fact_checking", "data_extraction"],
        "supported_input_types": ["text", "json"],
        "supported_output_types": ["json", "text"],
        "api_endpoint": None,
        "pricing_info": {"per_query": 0.001},
        "speed_rating": 9.0,
        "quality_rating": 9.0,
        "enabled": True,
        "priority": 1,
        "fallback_priority": 1,
        "executability_requires_auth": False
    },
    {
        "id": "dalle-3",
        "name": "OpenAI DALL-E 3 / Visual Art",
        "provider": "openai",
        "description": "Generates photorealistic images, conceptual art, slide graphics, and logos based on textual descriptions.",
        "category": "Image Generation",
        "capabilities": ["image_generation", "visual_art"],
        "supported_input_types": ["text"],
        "supported_output_types": ["image"],
        "api_endpoint": "https://api.openai.com/v1/images/generations",
        "pricing_info": {"per_image": 0.040},
        "speed_rating": 7.5,
        "quality_rating": 9.6,
        "enabled": True,
        "priority": 1,
        "fallback_priority": 2,
        "executability_requires_auth": True
    },
    {
        "id": "pollinations-image",
        "name": "LiteMind Free Art & Diagram Generator",
        "provider": "pollinations",
        "description": "Instant open-access image generator for slide visuals, logos, diagrams, and illustrations.",
        "category": "Image Generation",
        "capabilities": ["image_generation"],
        "supported_input_types": ["text"],
        "supported_output_types": ["image"],
        "api_endpoint": "https://image.pollinations.ai/prompt",
        "pricing_info": {"per_image": 0.00},
        "speed_rating": 9.0,
        "quality_rating": 8.2,
        "enabled": True,
        "priority": 2,
        "fallback_priority": 1,
        "executability_requires_auth": False
    },
    {
        "id": "presentation-engine-pptx",
        "name": "LiteMind Presentation Builder (.pptx)",
        "provider": "python_pptx",
        "description": "Compiles structured slide content, bullet points, headers, and images into native Microsoft PowerPoint PPTX files.",
        "category": "Presentation Generation",
        "capabilities": ["pptx_generation", "slide_layout"],
        "supported_input_types": ["json"],
        "supported_output_types": ["pptx"],
        "api_endpoint": None,
        "pricing_info": {"per_file": 0.00},
        "speed_rating": 10.0,
        "quality_rating": 9.5,
        "enabled": True,
        "priority": 1,
        "fallback_priority": 1,
        "executability_requires_auth": False
    },
    {
        "id": "document-engine-pdf-docx",
        "name": "LiteMind Document & PDF Generator",
        "provider": "reportlab",
        "description": "Generates publication-ready PDF reports and Microsoft Word DOCX files with formatted tables, titles, and headers.",
        "category": "Document Generation",
        "capabilities": ["pdf_generation", "docx_generation"],
        "supported_input_types": ["json", "text"],
        "supported_output_types": ["pdf", "docx"],
        "api_endpoint": None,
        "pricing_info": {"per_file": 0.00},
        "speed_rating": 10.0,
        "quality_rating": 9.5,
        "enabled": True,
        "priority": 1,
        "fallback_priority": 1,
        "executability_requires_auth": False
    },
    {
        "id": "quality-control-reviewer",
        "name": "LiteMind Quality Control & Evaluation Engine",
        "provider": "litemind_eval",
        "description": "Evaluates workflow outputs for accuracy, completeness, formatting, tone, and compliance with the user's initial goal.",
        "category": "Quality Control",
        "capabilities": ["quality_review", "fact_verification"],
        "supported_input_types": ["json", "text"],
        "supported_output_types": ["json"],
        "api_endpoint": None,
        "pricing_info": {"per_eval": 0.001},
        "speed_rating": 9.5,
        "quality_rating": 9.5,
        "enabled": True,
        "priority": 1,
        "fallback_priority": 1,
        "executability_requires_auth": False
    }
]


def seed_tools():
    init_db()
    db = SessionLocal()
    try:
        for tool_data in INITIAL_TOOLS:
            existing = db.query(Tool).filter(Tool.id == tool_data["id"]).first()
            if not existing:
                tool = Tool(**tool_data)
                db.add(tool)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed_tools()
    print("Tool Registry seeded successfully.")
