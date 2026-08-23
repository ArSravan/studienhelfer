from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError

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