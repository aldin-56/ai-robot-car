from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from litemind.database.models import Tool, UserConnection, UserSettings
from litemind.database.security import decrypt_secret
from litemind.adapters.providers import (
    LocalLLMAdapter,
    OpenAIAdapter,
    GeminiAdapter,
    ClaudeAdapter,
    WebResearchAdapter,
    PollinationsAdapter,
    PresentationAdapter,
    DocumentAdapter,
    QualityReviewAdapter
)

# Registry map of provider string to adapter instances
ADAPTER_MAP = {
    "local_llm": LocalLLMAdapter(),
    "openai": OpenAIAdapter(),
    "gemini": GeminiAdapter(),
    "anthropic": ClaudeAdapter(),
    "web_research": WebResearchAdapter(),
    "pollinations": PollinationsAdapter(),
    "python_pptx": PresentationAdapter(),
    "reportlab": DocumentAdapter(),
    "litemind_eval": QualityReviewAdapter()
}


class ToolRegistry:
    """
    Registry service responsible for querying available tools, evaluating connection status,
    calculating suitability scores, and resolving execution adapters.
    """

    @staticmethod
    def get_adapter(provider: str):
        return ADAPTER_MAP.get(provider, None)

    @staticmethod
    def get_user_connections(db: Session, user_id: str) -> Dict[str, UserConnection]:
        """Fetch active user provider connections indexed by provider name."""
        connections = db.query(UserConnection).filter(
            UserConnection.user_id == user_id,
            UserConnection.enabled == True
        ).all()
        return {conn.provider: conn for conn in connections}

    @staticmethod
    def get_decrypted_key(connection: UserConnection) -> Optional[str]:
        if not connection or not connection.encrypted_api_key:
            return None
        return decrypt_secret(connection.encrypted_api_key)

    @classmethod
    def list_tools_for_user(cls, db: Session, user_id: str) -> List[Dict[str, Any]]:
        """
        List all tools in registry enriched with user-specific connection status.
        Shows 'Connected ✓' or 'Not connected' explicitly without exposing secrets.
        """
        tools = db.query(Tool).filter(Tool.enabled == True).all()
        user_conns = cls.get_user_connections(db, user_id)

        result = []
        for tool in tools:
            tool_dict = {
                "id": tool.id,
                "name": tool.name,
                "provider": tool.provider,
                "description": tool.description,
                "category": tool.category,
                "capabilities": tool.capabilities,
                "supported_input_types": tool.supported_input_types,
                "supported_output_types": tool.supported_output_types,
                "pricing_info": tool.pricing_info,
                "speed_rating": tool.speed_rating,
                "quality_rating": tool.quality_rating,
                "enabled": tool.enabled,
                "priority": tool.priority,
                "fallback_priority": tool.fallback_priority,
                "executability_requires_auth": tool.executability_requires_auth
            }

            if not tool.executability_requires_auth:
                tool_dict["connection_status"] = "Connected"
                tool_dict["user_available"] = True
            elif tool.provider in user_conns and user_conns[tool.provider].status == "connected":
                tool_dict["connection_status"] = "Connected"
                tool_dict["user_available"] = True
            else:
                tool_dict["connection_status"] = "Not connected"
                tool_dict["user_available"] = False

            result.append(tool_dict)

        return result

    @classmethod
    def select_best_tool(
        cls,
        db: Session,
        user_id: str,
        category: str,
        required_capability: str,
        settings: Optional[UserSettings] = None,
        exclude_tool_ids: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Intelligently select the highest scoring connected tool based on:
        - Capability match
        - Quality vs Speed vs Cost optimization preferences
        - User provider preferences
        - Connection availability
        """
        exclude_set = set(exclude_tool_ids or [])
        tools = db.query(Tool).filter(Tool.enabled == True).all()
        user_conns = cls.get_user_connections(db, user_id)

        pref_mode = settings.optimization_preference if settings else "balanced"
        pref_providers = settings.preferred_providers if (settings and settings.preferred_providers) else []

        scored_tools = []

        for tool in tools:
            if tool.id in exclude_set:
                continue

            # Check if capabilities match
            if required_capability not in tool.capabilities and tool.category != category:
                continue

            # Check auth availability
            if tool.executability_requires_auth:
                conn = user_conns.get(tool.provider)
                if not conn or conn.status != "connected":
                    continue  # Only consider connected tools

            # Calculate Suitability Score (0 - 100)
            score = 50.0  # Base score

            # Capability match bonus
            if required_capability in tool.capabilities:
                score += 25.0

            # Quality / Speed / Cost weighting
            if pref_mode == "quality":
                score += tool.quality_rating * 3.0
            elif pref_mode == "speed":
                score += tool.speed_rating * 3.0
            elif pref_mode == "cost":
                # Free tools or lower pricing get boost
                if not tool.executability_requires_auth or tool.provider in ("pollinations", "web_research"):
                    score += 30.0
                else:
                    score += (10.0 - (tool.priority * 2.0))
            else:  # Balanced
                score += (tool.quality_rating * 1.5) + (tool.speed_rating * 1.0)

            # User preferred provider bonus
            if tool.provider in pref_providers:
                score += 15.0

            # Priority tie-breaker
            score -= (tool.priority * 2.0)

            reason = f"Selected {tool.name} for task category '{category}'. " \
                     f"Matches capability '{required_capability}' with suitability score {round(score, 1)}/100 " \
                     f"under '{pref_mode}' optimization."

            scored_tools.append({
                "tool": tool,
                "score": score,
                "reason": reason
            })

        if not scored_tools:
            return None

        # Sort descending by suitability score
        scored_tools.sort(key=lambda x: x["score"], reverse=True)
        best = scored_tools[0]

        conn = user_conns.get(best["tool"].provider)
        api_key = cls.get_decrypted_key(conn) if conn else None

        return {
            "tool": best["tool"],
            "score": best["score"],
            "reason": best["reason"],
            "api_key": api_key,
            "adapter": cls.get_adapter(best["tool"].provider)
        }
