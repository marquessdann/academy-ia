from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_admin
from app.database import get_db
from app.models.gym_schedule import GymSchedule
from app.repositories import schedule_repository
from app.schemas.gym_schedule import GymScheduleCreate, GymScheduleOut

router = APIRouter(prefix="/schedules", tags=["Grade horária (admin)"])


@router.get("", response_model=list[GymScheduleOut], dependencies=[Depends(get_current_admin)])
def list_schedules(db: Session = Depends(get_db)):
    return schedule_repository.list_all(db)


@router.post("", response_model=GymScheduleOut, status_code=201, dependencies=[Depends(get_current_admin)])
def create_schedule(payload: GymScheduleCreate, db: Session = Depends(get_db)):
    schedule = GymSchedule(**payload.model_dump())
    return schedule_repository.create(db, schedule)
