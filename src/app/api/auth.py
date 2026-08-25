from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy.orm import Session

from app.models import User
from app.core.database import get_db
from app.schemas.user import UserCreate, UserRead, UserLogin, Token
from app.services.user import create_user, authenticate_user
from app.core.security import create_access_token
from app.api.deps import get_current_user

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
    response_model=Token,
)

def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):

    user = authenticate_user(
        db,
        form_data.username,
        form_data.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(
        subject=str(user.user_id)
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
    )

@router.get(
    "/me",
    response_model=UserRead,
)
def me(
    current_user: User = Depends(get_current_user),
):
    return current_user