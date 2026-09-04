from datetime import datetime

from pydantic import BaseModel


class ClassOccupancy(BaseModel):
    class_id: int
    title: str
    start_time: datetime
    capacity: int
    booked_count: int
    occupancy_rate: float


class QuietSlot(BaseModel):
    day_of_week: int
    day_name: str
    hour: int
    average_occupancy_rate: float
    sample_size: int
