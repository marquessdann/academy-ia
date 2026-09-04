from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.gym_schedule import GymSchedule


def get_by_id(db: Session, schedule_id: int) -> GymSchedule | None:
    return db.get(GymSchedule, schedule_id)


def list_all(db: Session) -> list[GymSchedule]:
    return list(db.scalars(select(GymSchedule).order_by(GymSchedule.day_of_week, GymSchedule.start_time)))


def create(db: Session, schedule: GymSchedule) -> GymSchedule:
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule
