from datetime import time

from pydantic import BaseModel, ConfigDict


class GymScheduleCreate(BaseModel):
    category_id: int
    instructor_id: int
    day_of_week: int  # 0 = segunda ... 6 = domingo
    start_time: time
    end_time: time
    capacity: int = 20


class GymScheduleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    instructor_id: int
    day_of_week: int
    start_time: time
    end_time: time
    capacity: int
