from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.repositories import booking_repository
from app.schemas.booking import BookingOut
from app.schemas.user import UserOut

router = APIRouter(prefix="/users", tags=["Usuários"])


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/me/bookings", response_model=list[BookingOut])
def get_my_bookings(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return booking_repository.list_by_user(db, current_user.id)
