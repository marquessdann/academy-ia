from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.schemas.category import CategoryOut
from app.schemas.instructor import InstructorOut


class GymClassCreate(BaseModel):
    title: str
    category_id: int
    instructor_id: int
    start_time: datetime
    end_time: datetime
    capacity: int = 20

    @field_validator("end_time")
    @classmethod
    def end_after_start(cls, end_time: datetime, info):
        start_time = info.data.get("start_time")
        if start_time and end_time <= start_time:
            raise ValueError("end_time deve ser depois de start_time")
        return end_time

    @field_validator("capacity")
    @classmethod
    def capacity_positive(cls, capacity: int):
        if capacity <= 0:
            raise ValueError("capacity deve ser maior que zero")
        return capacity


class GymClassOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    start_time: datetime
    end_time: datetime
    capacity: int
    category: CategoryOut
    instructor: InstructorOut


class GymClassWithOccupancy(GymClassOut):
    booked_count: int
    available_spots: int
    is_full: bool
