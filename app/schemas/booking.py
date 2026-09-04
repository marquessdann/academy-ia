from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.booking import BookingStatus
from app.schemas.gym_class import GymClassOut


class BookingCreate(BaseModel):
    class_id: int


class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: BookingStatus
    created_at: datetime
    cancelled_at: datetime | None = None
    gym_class: GymClassOut
