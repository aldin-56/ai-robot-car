import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import UserCredential, Provider
from backend.security import encrypt_api_key, mask_api_key, decrypt_api_key
from backend.adapters.llm_adapter import LLMAdapter

router = APIRouter(prefix="/api/credentials", tags=["credentials"])


class SaveCredentialSchema(BaseModel):
    user_id: str = "default_demo_user"
    provider_id: str
    api_key: str


class TestCredentialSchema(BaseModel):
    user_id: str = "default_demo_user"
    provider_id: str


@router.get("")
def list_user_credentials(user_id: str = "default_demo_user", db: Session = Depends(get_db)):
    creds = db.query(UserCredential).filter(UserCredential.user_id == user_id).all()
    providers = db.query(Provider).all()

    connected_map = {c.provider_id: c for c in creds}

    results = []
    for p in providers:
        c = connected_map.get(p.id)
        is_connected = bool(c and c.status == "active")

        # Public providers are always connected
        if p.id in ["duckduckgo", "pollinations", "document_gen"]:
            is_connected = True

        masked_key = ""
        if c and c.encrypted_api_key:
            dec = decrypt_api_key(c.encrypted_api_key)
            masked_key = mask_api_key(dec)

        results.append({
            "provider_id": p.id,
            "provider_name": p.name,
            "description": p.description,
            "is_connected": is_connected,
            "masked_key": masked_key,
            "status": c.status if c else ("connected" if is_connected else "not_connected"),
            "last_tested_at": c.last_tested_at.isoformat() if (c and c.last_tested_at) else None
        })

    return results


@router.post("")
def save_credential(data: SaveCredentialSchema, db: Session = Depends(get_db)):
    existing = db.query(UserCredential).filter(
        UserCredential.user_id == data.user_id,
        UserCredential.provider_id == data.provider_id
    ).first()

    enc_key = encrypt_api_key(data.api_key.strip())

    if existing:
        existing.encrypted_api_key = enc_key
        existing.status = "active"
        existing.last_tested_at = datetime.datetime.utcnow()
    else:
        cred = UserCredential(
            user_id=data.user_id,
            provider_id=data.provider_id,
            encrypted_api_key=enc_key,
            status="active",
            last_tested_at=datetime.datetime.utcnow()
        )
        db.add(cred)

    db.commit()
    return {"message": f"Successfully connected API key for provider {data.provider_id}"}


@router.delete("/{provider_id}")
def remove_credential(provider_id: str, user_id: str = "default_demo_user", db: Session = Depends(get_db)):
    cred = db.query(UserCredential).filter(
        UserCredential.user_id == user_id,
        UserCredential.provider_id == provider_id
    ).first()

    if cred:
        db.delete(cred)
        db.commit()

    return {"message": f"Removed API connection for provider {provider_id}"}


@router.post("/test")
def test_connection(data: TestCredentialSchema, db: Session = Depends(get_db)):
    cred = db.query(UserCredential).filter(
        UserCredential.user_id == data.user_id,
        UserCredential.provider_id == data.provider_id
    ).first()

    if not cred and data.provider_id not in ["duckduckgo", "pollinations", "document_gen"]:
        raise HTTPException(status_code=400, detail="No connection configured for this provider.")

    raw_key = decrypt_api_key(cred.encrypted_api_key) if cred else "public"

    # Validate adapter connection
    if data.provider_id in ["openai", "gemini", "anthropic"]:
        model = "gemini-2.5-flash" if data.provider_id == "gemini" else ("gpt-4o-mini" if data.provider_id == "openai" else "claude-3-5-sonnet")
        adapter = LLMAdapter(provider_id=data.provider_id, model_name=model, api_key=raw_key)
        is_valid = adapter.authenticate()
    else:
        is_valid = True

    if cred:
        cred.status = "active" if is_valid else "invalid"
        cred.last_tested_at = datetime.datetime.utcnow()
        db.commit()

    return {
        "provider_id": data.provider_id,
        "is_valid": is_valid,
        "status": "connected" if is_valid else "connection_error"
    }
