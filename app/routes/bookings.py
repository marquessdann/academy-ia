from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.repositories import booking_repository
from app.schemas.booking import BookingCreate, BookingOut
from app.services import booking_service

router = APIRouter(prefix="/bookings", tags=["Reservas"])


@router.post("", response_model=BookingOut, status_code=201)
def create_booking(payload: BookingCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    booking = booking_service.create_booking(db, current_user.id, payload.class_id)
    return booking_repository.get_by_id(db, booking.id)


@router.delete("/{booking_id}", response_model=BookingOut)
def cancel_booking(booking_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    booking = booking_service.cancel_booking(db, current_user.id, booking_id)
    return booking_repository.get_by_id(db, booking.id)
