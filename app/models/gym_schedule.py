from sqlalchemy import ForeignKey, Integer, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class GymSchedule(Base):
    """Grade horária recorrente (ex.: Funcional toda terça às 19h).

    Serve de modelo para gerar aulas (GymClass) em datas específicas.
    """

    __tablename__ = "gym_schedules"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    instructor_id: Mapped[int] = mapped_column(ForeignKey("instructors.id"), nullable=False)
    # 0 = segunda-feira ... 6 = domingo (padrão datetime.weekday())
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[Time] = mapped_column(Time, nullable=False)
    end_time: Mapped[Time] = mapped_column(Time, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=20)

    category: Mapped["Category"] = relationship()
    instructor: Mapped["Instructor"] = relationship()
    classes: Mapped[list["GymClass"]] = relationship(back_populates="schedule")
