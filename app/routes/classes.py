from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_admin
from app.database import get_db
from app.models.gym_class import GymClass
from app.repositories import class_repository
from app.schemas.gym_class import GymClassCreate, GymClassWithOccupancy

router = APIRouter(prefix="/classes", tags=["Aulas"])


def _with_occupancy(db: Session, gym_class: GymClass) -> GymClassWithOccupancy:
    booked = class_repository.count_active_bookings(db, gym_class.id)
    return GymClassWithOccupancy(
        id=gym_class.id,
        title=gym_class.title,
        start_time=gym_class.start_time,
        end_time=gym_class.end_time,
        capacity=gym_class.capacity,
        category=gym_class.category,
        instructor=gym_class.instructor,
        booked_count=booked,
        available_spots=gym_class.capacity - booked,
        is_full=booked >= gym_class.capacity,
    )


@router.get("", response_model=list[GymClassWithOccupancy])
def list_classes(
    category_id: int | None = None,
    start_after: datetime | None = None,
    start_before: datetime | None = None,
    db: Session = Depends(get_db),
):
    classes = class_repository.list_classes(db, category_id=category_id, start_after=start_after, start_before=start_before)
    return [_with_occupancy(db, gym_class) for gym_class in classes]


@router.get("/{class_id}", response_model=GymClassWithOccupancy)
def get_class(class_id: int, db: Session = Depends(get_db)):
    gym_class = class_repository.get_by_id(db, class_id)
    if gym_class is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aula não encontrada")
    return _with_occupancy(db, gym_class)


@router.post("", response_model=GymClassWithOccupancy, status_code=201, dependencies=[Depends(get_current_admin)])
def create_class(payload: GymClassCreate, db: Session = Depends(get_db)):
    gym_class = GymClass(**payload.model_dump())
    gym_class = class_repository.create(db, gym_class)
    gym_class = class_repository.get_by_id(db, gym_class.id)
    return _with_occupancy(db, gym_class)
