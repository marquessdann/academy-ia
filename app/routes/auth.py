from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.jwt_handler import create_access_token
from app.auth.security import hash_password, verify_password
from app.database import get_db
from app.models.user import User
from app.repositories import user_repository
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserCreate, UserOut

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if user_repository.get_by_email(db, payload.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Este e-mail já está cadastrado")

    user = User(name=payload.name, email=payload.email, hashed_password=hash_password(payload.password))
    return user_repository.create(db, user)


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = user_repository.get_by_email(db, payload.email)
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou senha inválidos")

    token = create_access_token(subject=str(user.id), role=user.role.value)
    return Token(access_token=token)
