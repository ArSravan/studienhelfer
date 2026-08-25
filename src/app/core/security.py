from datetime import datetime, timedelta, timezone

import jwt

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError

from app.core.config import settings

password_hasher = PasswordHasher()

DUMMY_HASH = password_hasher.hash(
    "dummy-password-that-is-never-used"
)

def hash_password(plain: str) -> str:
    return password_hasher.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return password_hasher.verify(hashed, plain)
    except (VerifyMismatchError, VerificationError):
        return False

def create_access_token(subject: str) -> str:
    now = datetime.now(timezone.utc)

    expires = now + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": subject,
        "iat": now,
        "exp": expires,
    }

    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    return token