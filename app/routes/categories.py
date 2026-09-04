from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_admin
from app.database import get_db
from app.models.category import Category
from app.repositories import category_repository
from app.schemas.category import CategoryCreate, CategoryOut

router = APIRouter(prefix="/categories", tags=["Modalidades"])


@router.get("", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return category_repository.list_all(db)


@router.post("", response_model=CategoryOut, status_code=201, dependencies=[Depends(get_current_admin)])
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)):
    category = Category(**payload.model_dump())
    return category_repository.create(db, category)
