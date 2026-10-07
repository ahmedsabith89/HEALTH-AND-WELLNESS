import os
import hashlib
import hmac
import secrets
import time
import json
import base64
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = os.environ.get("SECRET_KEY", "class-presentation-hub-super-secret-key-2026")
TOKEN_EXPIRY_SECONDS = 7 * 24 * 3600  # 7 days

def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with random salt."""
    salt = secrets.token_hex(16)
    iterations = 100_000
    derived = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        iterations
    )
    return f"{salt}${iterations}${derived.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against stored salt and hash."""
    try:
        parts = hashed_password.split('$')
        if len(parts) != 3:
            return False
        salt, iterations_str, derived_hex = parts
        iterations = int(iterations_str)
        test_derived = hashlib.pbkdf2_hmac(
            'sha256',
            plain_password.encode('utf-8'),
            salt.encode('utf-8'),
            iterations
        )
        return hmac.compare_digest(test_derived.hex(), derived_hex)
    except Exception:
        return False

def create_session_token(payload: Dict[str, Any]) -> str:
    """Create a tamper-proof signed JSON token."""
    payload_copy = payload.copy()
    payload_copy["exp"] = int(time.time()) + TOKEN_EXPIRY_SECONDS
    raw_json = json.dumps(payload_copy, separators=(',', ':'), sort_keys=True)
    b64_payload = base64.urlsafe_b64encode(raw_json.encode('utf-8')).decode('utf-8').rstrip('=')
    signature = hmac.new(SECRET_KEY.encode('utf-8'), b64_payload.encode('utf-8'), hashlib.sha256).hexdigest()
    return f"{b64_payload}.{signature}"

def verify_session_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify signed token signature and expiration."""
    try:
        parts = token.split('.')
        if len(parts) != 2:
            return None
        b64_payload, signature = parts
        expected_sig = hmac.new(SECRET_KEY.encode('utf-8'), b64_payload.encode('utf-8'), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected_sig, signature):
            return None
        # Add padding back if needed
        padding = 4 - (len(b64_payload) % 4)
        if padding != 4:
            b64_payload += '=' * padding
        raw_json = base64.urlsafe_b64decode(b64_payload.encode('utf-8')).decode('utf-8')
        data = json.loads(raw_json)
        if data.get("exp", 0) < int(time.time()):
            return None
        return data
    except Exception:
        return None

security = HTTPBearer(auto_error=False)

def get_current_user(request: Request, creds: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
    """Retrieve current user from cookie or Authorization header."""
    token = None
    if creds:
        token = creds.credentials
    if not token:
        token = request.cookies.get("session_token")
    if not token:
        # Check Authorization header without bearer if present
        auth_hdr = request.headers.get("Authorization")
        if auth_hdr and auth_hdr.startswith("Bearer "):
            token = auth_hdr.split(" ", 1)[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_data = verify_session_token(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return user_data

def require_admin(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if user.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user

def require_student(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if user.get("role") != "STUDENT":
        raise HTTPException(status_code=403, detail="Student privileges required")
    return user
