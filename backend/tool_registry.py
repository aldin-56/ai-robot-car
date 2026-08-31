import os
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.models import Provider, Tool, UserCredential
from backend.security import decrypt_api_key

DEFAULT_PROVIDERS = [
    {"id": "gemini", "name": "Google Gemini", "description": "Google's powerful multimodal and reasoning model suite", "website": "https://aistudio.google.com"},
    {"id": "openai", "name": "OpenAI", "description": "Industry leading GPT language and DALL-E image models", "website": "https://openai.com"},
    {"id": "anthropic", "name": "Anthropic Claude", "description": "Advanced reasoning and safe AI assistance", "website": "https://anthropic.com"},
    {"id": "duckduckgo", "name": "DuckDuckGo Search", "description": "Real-time web search and content discovery", "website": "https://duckduckgo.com"},
    {"id": "pollinations", "name": "Pollinations AI", "description": "Free open image generation engine", "website": "https://pollinations.ai"},
    {"id": "document_gen", "name": "LiteMind Document Suite", "description": "Native PPTX, PDF, and DOCX generation engines", "website": "https://litemind.ai"}
]

DEFAULT_TOOLS = [
    {
        "id": "gemini_25_flash",
        "name": "Gemini 2.5 Flash",
        "provider": "gemini",
        "description": "Fast multimodal LLM with high reasoning quality and speed.",
        "category": "LLM",
        "capabilities": ["text", "reasoning", "multimodal", "coding", "research"],
        "supported_input_types": ["text", "image", "pdf", "json"],
        "supported_output_types": ["text", "markdown", "json"],
        "api_endpoint": "https://generativelanguage.googleapis.com",
        "pricing_info": {"input_cost_per_1k": 0.0001, "output_cost_per_1k": 0.0003},
        "speed_rating": 9.5,
        "quality_rating": 9.0,
        "is_enabled": True,
        "priority": 10,
        "fallback_priority": 8
    },
    {
        "id": "gemini_25_pro",
        "name": "Gemini 2.5 Pro",
        "provider": "gemini",
        "description": "Ultra-capable reasoning and analysis LLM for complex tasks.",
        "category": "LLM",
        "capabilities": ["text", "reasoning", "multimodal", "coding", "complex_analysis"],
        "supported_input_types": ["text", "image", "pdf", "csv", "json"],
        "supported_output_types": ["text", "markdown", "json"],
        "api_endpoint": "https://generativelanguage.googleapis.com",
        "pricing_info": {"input_cost_per_1k": 0.00125, "output_cost_per_1k": 0.005},
        "speed_rating": 7.5,
        "quality_rating": 9.8,
        "is_enabled": True,
        "priority": 9,
        "fallback_priority": 9
    },
    {
        "id": "openai_gpt4o",
        "name": "GPT-4o",
        "provider": "openai",
        "description": "OpenAI flagship omni model for complex writing and reasoning.",
        "category": "LLM",
        "capabilities": ["text", "reasoning", "coding"],
        "supported_input_types": ["text", "image", "json"],
        "supported_output_types": ["text", "markdown", "json"],
        "api_endpoint": "https://api.openai.com/v1/chat/completions",
        "pricing_info": {"input_cost_per_1k": 0.0025, "output_cost_per_1k": 0.010},
        "speed_rating": 8.5,
        "quality_rating": 9.6,
        "is_enabled": True,
        "priority": 8,
        "fallback_priority": 7
    },
    {
        "id": "openai_dalle3",
        "name": "DALL-E 3",
        "provider": "openai",
        "description": "High fidelity AI image generation model.",
        "category": "Image Generation",
        "capabilities": ["image_generation"],
        "supported_input_types": ["text"],
        "supported_output_types": ["image"],
        "api_endpoint": "https://api.openai.com/v1/images/generations",
        "pricing_info": {"cost_per_image": 0.040},
        "speed_rating": 7.0,
        "quality_rating": 9.5,
        "is_enabled": True,
        "priority": 8,
        "fallback_priority": 5
    },
    {
        "id": "duckduckgo_search",
        "name": "DuckDuckGo Web Search & Scraper",
        "provider": "duckduckgo",
        "description": "Real-time search engine for fresh facts and live information.",
        "category": "Research",
        "capabilities": ["search", "web_scraping", "fact_checking"],
        "supported_input_types": ["text"],
        "supported_output_types": ["text", "json"],
        "api_endpoint": "duckduckgo_api",
        "pricing_info": {"cost_per_query": 0.0},
        "speed_rating": 8.0,
        "quality_rating": 8.5,
        "is_enabled": True,
        "priority": 10,
        "fallback_priority": 10
    },
    {
        "id": "pollinations_image",
        "name": "Pollinations Image Engine",
        "provider": "pollinations",
        "description": "Fast and open image synthesis service.",
        "category": "Image Generation",
        "capabilities": ["image_generation"],
        "supported_input_types": ["text"],
        "supported_output_types": ["image"],
        "api_endpoint": "https://image.pollinations.ai",
        "pricing_info": {"cost_per_image": 0.0},
        "speed_rating": 9.0,
        "quality_rating": 8.0,
        "is_enabled": True,
        "priority": 9,
        "fallback_priority": 10
    },
    {
        "id": "pptx_generator",
        "name": "PowerPoint Presentation Engine",
        "provider": "document_gen",
        "description": "Native PPTX slide presentation builder.",
        "category": "Presentation Generation",
        "capabilities": ["presentation_generation", "pptx"],
        "supported_input_types": ["json", "text"],
        "supported_output_types": ["pptx"],
        "api_endpoint": "internal_pptx",
        "pricing_info": {"cost_per_doc": 0.0},
        "speed_rating": 9.5,
        "quality_rating": 9.0,
        "is_enabled": True,
        "priority": 10,
        "fallback_priority": 10
    },
    {
        "id": "pdf_generator",
        "name": "PDF Report Engine",
        "provider": "document_gen",
        "description": "Native ReportLab PDF document builder.",
        "category": "Document Generation",
        "capabilities": ["pdf_generation", "pdf"],
        "supported_input_types": ["json", "text"],
        "supported_output_types": ["pdf"],
        "api_endpoint": "internal_pdf",
        "pricing_info": {"cost_per_doc": 0.0},
        "speed_rating": 9.5,
        "quality_rating": 9.0,
        "is_enabled": True,
        "priority": 10,
        "fallback_priority": 10
    }
]


class ToolRegistry:
    """Manages available tools, API credentials, and intelligent tool selection scoring."""

    def __init__(self, db: Session):
        self.db = db
        self._ensure_default_seed()

    def _ensure_default_seed(self):
        """Seed default providers and tools into database if empty."""
        if self.db.query(Provider).count() == 0:
            for p in DEFAULT_PROVIDERS:
                self.db.add(Provider(**p))
            self.db.commit()

        if self.db.query(Tool).count() == 0:
            for t in DEFAULT_TOOLS:
                self.db.add(Tool(**t))
            self.db.commit()

    def get_user_connected_providers(self, user_id: str) -> Dict[str, str]:
        """Returns a dict mapping provider_id -> decrypted API key for a user."""
        credentials = self.db.query(UserCredential).filter(
            UserCredential.user_id == user_id,
            UserCredential.status == "active"
        ).all()

        connected = {}
        for c in credentials:
            key = decrypt_api_key(c.encrypted_api_key)
            if key:
                connected[c.provider_id] = key

        # Public / zero-auth providers are always available
        connected["duckduckgo"] = "public"
        connected["pollinations"] = "public"
        connected["document_gen"] = "internal"

        # Check environment variables as well for default system connections
        env_gemini = os.getenv("GEMINI_API_KEY")
        if env_gemini and "gemini" not in connected:
            connected["gemini"] = env_gemini

        env_openai = os.getenv("OPENAI_API_KEY")
        if env_openai and "openai" not in connected:
            connected["openai"] = env_openai

        return connected

    def select_best_tool(
        self,
        required_capability: str,
        user_id: str,
        optimization_pref: str = "balanced",
        excluded_tool_ids: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Calculates suitability score for each tool matching capability and returns best match + reason."""
        excluded = set(excluded_tool_ids or [])
        connected_providers = self.get_user_connected_providers(user_id)

        all_tools = self.db.query(Tool).filter(Tool.is_enabled == True).all()
        candidate_scores = []

        for tool in all_tools:
            if tool.id in excluded:
                continue

            # Check capability match
            caps = tool.capabilities or []
            if required_capability not in caps and tool.category.lower() != required_capability.lower():
                continue

            # Check provider connection status
            is_connected = tool.provider in connected_providers
            if not is_connected:
                continue

            # Calculate suitability score (0 - 100)
            score = 50.0  # Base score

            # 1. Quality Rating (1 to 10) -> up to +25
            score += (tool.quality_rating or 8.0) * 2.5

            # 2. Speed Rating (1 to 10) -> up to +15
            score += (tool.speed_rating or 8.0) * 1.5

            # 3. Priority weighting -> up to +10
            score += (tool.priority or 5)

            # 4. Apply User Preferences weighting
            if optimization_pref == "best_quality":
                score += (tool.quality_rating or 8.0) * 3.0
            elif optimization_pref == "fastest":
                score += (tool.speed_rating or 8.0) * 3.0
            elif optimization_pref == "lowest_cost":
                # Prefer tools with lower cost
                pricing = tool.pricing_info or {}
                cost = pricing.get("input_cost_per_1k", 0) + pricing.get("cost_per_image", 0)
                if cost == 0:
                    score += 20.0
                else:
                    score -= cost * 1000

            candidate_scores.append({
                "tool": tool,
                "score": score,
                "api_key": connected_providers.get(tool.provider)
            })

        if not candidate_scores:
            return None

        # Sort by score descending
        candidate_scores.sort(key=lambda x: x["score"], reverse=True)
        best = candidate_scores[0]
        tool_obj = best["tool"]

        reason = (
            f"Selected '{tool_obj.name}' (Provider: {tool_obj.provider.upper()}) "
            f"because it supports required capability '{required_capability}' with high quality rating ({tool_obj.quality_rating}/10) "
            f"and active connection status."
        )

        return {
            "tool_id": tool_obj.id,
            "tool_name": tool_obj.name,
            "provider": tool_obj.provider,
            "api_key": best["api_key"],
            "score": best["score"],
            "reason": reason,
            "tool": tool_obj
        }
