from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_admin, get_current_user
from app.database import get_db
from app.schemas.analytics import ClassOccupancy, QuietSlot
from app.services import analytics_service, recommendation_service

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/occupancy", response_model=list[ClassOccupancy], dependencies=[Depends(get_current_admin)])
def get_occupancy(db: Session = Depends(get_db)):
    """Relatório de ocupação de todas as aulas (área administrativa)."""
    return analytics_service.get_occupancy_report(db)


@router.get("/quietest-times", response_model=list[QuietSlot], dependencies=[Depends(get_current_admin)])
def get_quietest_times(db: Session = Depends(get_db)):
    """Horários historicamente menos concorridos (área administrativa)."""
    return analytics_service.get_quietest_slots(db)


@router.get("/recommendations", dependencies=[Depends(get_current_user)])
def get_recommendations(category_id: int | None = None, db: Session = Depends(get_db)):
    """Recomendação de melhores horários para treinar, disponível para qualquer aluno logado."""
    return recommendation_service.recommend_best_times(db, category_id=category_id)
