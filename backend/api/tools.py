from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Tool, Provider
from backend.tool_registry import ToolRegistry

router = APIRouter(prefix="/api/tools", tags=["tools"])


@router.get("")
def list_marketplace_tools(user_id: str = "default_demo_user", db: Session = Depends(get_db)):
    registry = ToolRegistry(db)
    connected_providers = registry.get_user_connected_providers(user_id)

    tools = db.query(Tool).all()
    results = []

    for t in tools:
        is_connected = t.provider in connected_providers
        results.append({
            "id": t.id,
            "name": t.name,
            "provider": t.provider,
            "description": t.description,
            "category": t.category,
            "capabilities": t.capabilities,
            "supported_input_types": t.supported_input_types,
            "supported_output_types": t.supported_output_types,
            "pricing_info": t.pricing_info,
            "speed_rating": t.speed_rating,
            "quality_rating": t.quality_rating,
            "is_enabled": t.is_enabled,
            "is_connected": is_connected
        })

    return results
