from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Category(Base):
    """Modalidade da academia: musculação, funcional, spinning, yoga, etc."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    classes: Mapped[list["GymClass"]] = relationship(back_populates="category")
