
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import hash_password, verify_password, DUMMY_HASH

def create_user(db: Session, user_data: UserCreate) -> User:
    existing_user = db.execute(
        select(User).where(User.email == user_data.email)
    ).scalar_one_or_none()

    if existing_user:
        raise ValueError("Email already registered")

    password_hash = hash_password(user_data.password)

    user = User(
        email=user_data.email,
        password_hash= password_hash,
    )

    db.add(user)

    try:
        db.commit() 
    except IntegrityError:
        db.rollback()
        raise ValueError("Email already registered")

    db.refresh(user)

    return user

def authenticate_user(
        db: Session,
        email: str,
        password: str
) -> User | None:

    user = db.execute(
        select(User).where(User.email == email)
    ).scalar_one_or_none()

    if user is None:
        verify_password(password, DUMMY_HASH)
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user