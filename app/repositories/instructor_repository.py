from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.instructor import Instructor


def get_by_id(db: Session, instructor_id: int) -> Instructor | None:
    return db.get(Instructor, instructor_id)


def list_all(db: Session) -> list[Instructor]:
    return list(db.scalars(select(Instructor).order_by(Instructor.name)))


def create(db: Session, instructor: Instructor) -> Instructor:
    db.add(instructor)
    db.commit()
    db.refresh(instructor)
    return instructor
