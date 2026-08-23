from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.user import UserCreate, UserRead, UserLogin
from app.services.user import create_user, authenticate_user

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

@router.post(
        "/register",
        response_model=UserRead,
        status_code=status.HTTP_201_CREATED,
)

def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    try:
        user = create_user(db, user_data)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    return user

@router.post(
    "/login",
    response_model=UserRead,
)

def login(
    user_data: UserLogin,
    db: Session = Depends(get_db),
):

    user = authenticate_user(
        db,
        user_data.email,
        user_data.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    return user