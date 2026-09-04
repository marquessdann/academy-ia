from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.booking import Booking, BookingStatus
from app.repositories import booking_repository, class_repository


class BookingError(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


def create_booking(db: Session, user_id: int, class_id: int) -> Booking:
    gym_class = class_repository.get_by_id(db, class_id)
    if gym_class is None:
        raise BookingError(status.HTTP_404_NOT_FOUND, "Aula não encontrada")

    if gym_class.start_time < datetime.now(timezone.utc).replace(tzinfo=None):
        raise BookingError(status.HTTP_400_BAD_REQUEST, "Não é possível reservar uma aula que já ocorreu")

    existing_booking = booking_repository.get_active_booking(db, user_id, class_id)
    if existing_booking is not None:
        raise BookingError(status.HTTP_409_CONFLICT, "Você já possui uma reserva ativa para esta aula")

    booked_count = class_repository.count_active_bookings(db, class_id)
    if booked_count >= gym_class.capacity:
        raise BookingError(status.HTTP_409_CONFLICT, "Aula lotada, não há vagas disponíveis")

    booking = Booking(user_id=user_id, class_id=class_id, status=BookingStatus.CONFIRMED)
    return booking_repository.create(db, booking)


def cancel_booking(db: Session, user_id: int, booking_id: int) -> Booking:
    booking = booking_repository.get_by_id(db, booking_id)
    if booking is None or booking.user_id != user_id:
        raise BookingError(status.HTTP_404_NOT_FOUND, "Reserva não encontrada")

    if booking.status == BookingStatus.CANCELLED:
        raise BookingError(status.HTTP_400_BAD_REQUEST, "Esta reserva já está cancelada")

    booking.status = BookingStatus.CANCELLED
    booking.cancelled_at = datetime.now(timezone.utc)
    return booking_repository.save(db, booking)
