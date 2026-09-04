from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.booking import Booking, BookingStatus
from app.models.gym_class import GymClass


def _base_query():
    return select(Booking).options(
        joinedload(Booking.gym_class).joinedload(GymClass.category),
        joinedload(Booking.gym_class).joinedload(GymClass.instructor),
    )


def get_by_id(db: Session, booking_id: int) -> Booking | None:
    return db.scalar(_base_query().where(Booking.id == booking_id))


def get_active_booking(db: Session, user_id: int, class_id: int) -> Booking | None:
    return db.scalar(
        select(Booking).where(
            Booking.user_id == user_id,
            Booking.class_id == class_id,
            Booking.status == BookingStatus.CONFIRMED,
        )
    )


def list_by_user(db: Session, user_id: int, status: BookingStatus | None = None) -> list[Booking]:
    query = _base_query().where(Booking.user_id == user_id).order_by(Booking.created_at.desc())
    if status is not None:
        query = query.where(Booking.status == status)
    return list(db.scalars(query).unique())


def create(db: Session, booking: Booking) -> Booking:
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def save(db: Session, booking: Booking) -> Booking:
    db.commit()
    db.refresh(booking)
    return booking
