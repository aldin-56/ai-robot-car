import pytest
from backend.database import Base, engine, SessionLocal
from backend.models import User, Provider, Tool, UserCredential, Project, Workflow, Task
from backend.security import encrypt_api_key, decrypt_api_key, mask_api_key


def test_db_and_security():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Test Security
    secret = "sk-proj-test1234567890abcdef"
    encrypted = encrypt_api_key(secret)
    assert encrypted != secret
    decrypted = decrypt_api_key(encrypted)
    assert decrypted == secret
    masked = mask_api_key(secret)
    assert masked == "sk-p....cdef"

    # Test DB insertion
    user = User(
        email="test@litemind.ai",
        username="testuser",
        hashed_password="hashed_pw_here"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    assert user.id is not None
    assert user.email == "test@litemind.ai"

    # Clean up
    db.delete(user)
    db.commit()
    db.close()
    print("DB and Security verification passed successfully!")


if __name__ == "__main__":
    test_db_and_security()
