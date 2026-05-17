import os
from datetime import datetime, timedelta, timezone

import jwt

SECRET = os.getenv("JWT_SECRET", "fallback-secret-change-this")
ALGORITHM = "HS256"
EXPIRE_DAYS = 30


def create_token() -> str:
    payload = {
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(days=EXPIRE_DAYS),
    }
    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)


def verify_token(token: str) -> bool:
    try:
        jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        return True
    except jwt.PyJWTError:
        return False
