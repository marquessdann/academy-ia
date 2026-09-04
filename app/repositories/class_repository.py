from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.booking import Booking, BookingStatus
from app.models.gym_class import GymClass


def _base_query():
    return select(GymClass).options(
        joinedload(GymClass.category), joinedload(GymClass.instructor)
    )


def get_by_id(db: Session, class_id: int) -> GymClass | None:
    return db.scalar(_base_query().where(GymClass.id == class_id))


def list_classes(
    db: Session,
    category_id: int | None = None,
    start_after: datetime | None = None,
    start_before: datetime | None = None,
) -> list[GymClass]:
    query = _base_query().order_by(GymClass.start_time)
    if category_id is not None:
        query = query.where(GymClass.category_id == category_id)
    if start_after is not None:
        query = query.where(GymClass.start_time >= start_after)
    if start_before is not None:
        query = query.where(GymClass.start_time <= start_before)
    return list(db.scalars(query).unique())


def count_active_bookings(db: Session, class_id: int) -> int:
    return db.scalar(
        select(func.count())
        .select_from(Booking)
        .where(Booking.class_id == class_id, Booking.status == BookingStatus.CONFIRMED)
    ) or 0


def create(db: Session, gym_class: GymClass) -> GymClass:
    db.add(gym_class)
    db.commit()
    db.refresh(gym_class)
    return gym_class
