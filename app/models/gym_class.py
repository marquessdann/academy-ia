from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class GymClass(Base):
    """Uma aula concreta, com data e horário definidos, que pode ser reservada."""

    __tablename__ = "gym_classes"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    instructor_id: Mapped[int] = mapped_column(ForeignKey("instructors.id"), nullable=False)
    schedule_id: Mapped[int | None] = mapped_column(ForeignKey("gym_schedules.id"), nullable=True)

    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=20)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    category: Mapped["Category"] = relationship(back_populates="classes")
    instructor: Mapped["Instructor"] = relationship(back_populates="classes")
    schedule: Mapped["GymSchedule"] = relationship(back_populates="classes")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="gym_class", cascade="all, delete-orphan")
