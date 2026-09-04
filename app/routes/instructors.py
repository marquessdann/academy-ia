from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_admin
from app.database import get_db
from app.models.instructor import Instructor
from app.repositories import instructor_repository
from app.schemas.instructor import InstructorCreate, InstructorOut

router = APIRouter(prefix="/instructors", tags=["Professores"])


@router.get("", response_model=list[InstructorOut])
def list_instructors(db: Session = Depends(get_db)):
    return instructor_repository.list_all(db)


@router.post("", response_model=InstructorOut, status_code=201, dependencies=[Depends(get_current_admin)])
def create_instructor(payload: InstructorCreate, db: Session = Depends(get_db)):
    instructor = Instructor(**payload.model_dump())
    return instructor_repository.create(db, instructor)
