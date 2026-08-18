import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..db.models import LoginModel
from ..schemas.api_models import UserRegisterRequest


AUTH_SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "care-outreach-secret-healthcare-token-key-2026")
TOKEN_EXPIRY_SECONDS = 86400 * 7  # 7 days


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 with a secure random salt."""
    salt = secrets.token_hex(16)
    iterations = 100_000
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations
    )
    return f"pbkdf2:sha256:{iterations}${salt}${derived.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hashed representation."""
    try:
        if not hashed_password or "$" not in hashed_password:
            return False
        algorithm_part, salt, original_hash = hashed_password.split("$", 2)
        _, _, iterations_str = algorithm_part.split(":")
        iterations = int(iterations_str)
        derived = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations
        )
        return hmac.compare_digest(derived.hex(), original_hash)
    except Exception:
        return False


def create_access_token(user_id: int, username: str, role: str, full_name: Optional[str] = None) -> str:
    """Create a tamper-proof HMAC-signed token payload."""
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "full_name": full_name or username,
        "exp": int(time.time()) + TOKEN_EXPIRY_SECONDS,
        "iat": int(time.time()),
    }
    payload_bytes = json.dumps(payload, separators=(',', ':')).encode("utf-8")
    encoded_payload = base64.urlsafe_b64encode(payload_bytes).decode("utf-8").rstrip("=")
    
    signature = hmac.new(
        AUTH_SECRET_KEY.encode("utf-8"),
        encoded_payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    
    return f"{encoded_payload}.{signature}"


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify signature and expiration of an access token."""
    try:
        if not token or "." not in token:
            return None
        encoded_payload, signature = token.split(".", 1)
        expected_sig = hmac.new(
            AUTH_SECRET_KEY.encode("utf-8"),
            encoded_payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_sig):
            return None
        
        # Add back base64 padding if needed
        padding = 4 - (len(encoded_payload) % 4)
        if padding != 4:
            encoded_payload += "=" * padding
            
        payload_bytes = base64.urlsafe_b64decode(encoded_payload.encode("utf-8"))
        payload = json.loads(payload_bytes.decode("utf-8"))
        
        if payload.get("exp", 0) < int(time.time()):
            return None
            
        return payload
    except Exception:
        return None


def register_user(db: Session, req: UserRegisterRequest) -> LoginModel:
    """Create a new user in the SQL login table."""
    # Check if username or email already exists
    existing = db.query(LoginModel).filter(
        or_(
            LoginModel.username == req.username.strip(),
            (LoginModel.email == req.email.strip()) if req.email else False
        )
    ).first()
    if existing:
        if existing.username == req.username.strip():
            raise ValueError(f"Username '{req.username}' is already taken.")
        else:
            raise ValueError(f"Email '{req.email}' is already registered.")

    hashed = hash_password(req.password)
    user = LoginModel(
        username=req.username.strip(),
        password_hash=hashed,
        email=req.email.strip() if req.email else None,
        full_name=req.full_name.strip() if req.full_name else req.username.strip(),
        role=req.role.strip() if req.role else "Care Manager",
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username_or_email: str, password: str) -> Optional[LoginModel]:
    """Authenticate user credentials against the SQL login table."""
    identifier = username_or_email.strip()
    user = db.query(LoginModel).filter(
        or_(
            LoginModel.username == identifier,
            LoginModel.email == identifier
        )
    ).first()
    
    if not user:
        return None
        
    if not verify_password(password, user.password_hash):
        return None
        
    # Update last_login timestamp
    user.last_login = datetime.now(timezone.utc)
    try:
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        
    return user


def get_user_by_id(db: Session, user_id: int) -> Optional[LoginModel]:
    """Retrieve user from SQL login table by ID."""
    return db.query(LoginModel).filter(LoginModel.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[LoginModel]:
    """Retrieve user from SQL login table by username."""
    return db.query(LoginModel).filter(LoginModel.username == username).first()
