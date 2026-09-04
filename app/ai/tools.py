"""Camada de "tools" (function calling) que a IA usa para consultar dados reais.

Cada função aqui é uma consulta segura e controlada ao banco de dados: a IA
nunca executa SQL livre, ela apenas chama estas funções com parâmetros
estruturados. Isso evita respostas inventadas e mantém o assistente restrito
aos dados reais da aplicação.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.booking import BookingStatus
from app.models.category import Category
from app.models.instructor import Instructor
from app.repositories.class_repository import count_active_bookings, list_classes
from app.services.analytics_service import get_quietest_slots
from app.repositories.booking_repository import list_by_user

PERIOD_RANGES = {
    "morning": (6, 12),
    "afternoon": (12, 18),
    "evening": (18, 23),
}


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _resolve_day(date_str: str | None) -> datetime:
    today = _now().replace(hour=0, minute=0, second=0, microsecond=0)
    if not date_str or date_str == "today":
        return today
    if date_str == "tomorrow":
        return today + timedelta(days=1)
    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        return today


def _resolve_category_id(db: Session, category_name: str | None) -> int | None:
    if not category_name:
        return None
    category = (
        db.query(Category)
        .filter(Category.name.ilike(f"%{category_name}%"))
        .first()
    )
    return category.id if category else None


def _resolve_instructor_id(db: Session, instructor_name: str | None) -> int | None:
    if not instructor_name:
        return None
    instructor = (
        db.query(Instructor)
        .filter(Instructor.name.ilike(f"%{instructor_name}%"))
        .first()
    )
    return instructor.id if instructor else None


def get_available_classes(
    db: Session,
    category: str | None = None,
    instructor: str | None = None,
    date: str | None = None,
    period: str | None = None,
) -> list[dict]:
    """Lista aulas futuras com vagas disponíveis, filtrando por modalidade, professor, data e período do dia."""
    category_id = _resolve_category_id(db, category)
    instructor_id = _resolve_instructor_id(db, instructor)
    day = _resolve_day(date)
    start = day
    end = day + timedelta(days=1)

    if period in PERIOD_RANGES:
        hour_start, hour_end = PERIOD_RANGES[period]
        start = day.replace(hour=hour_start)
        end = day.replace(hour=hour_end)

    classes = list_classes(db, category_id=category_id, start_after=max(start, _now()), start_before=end)
    if instructor_id is not None:
        classes = [c for c in classes if c.instructor_id == instructor_id]

    result = []
    for gym_class in classes:
        booked = count_active_bookings(db, gym_class.id)
        available = gym_class.capacity - booked
        if available > 0:
            result.append(
                {
                    "class_id": gym_class.id,
                    "title": gym_class.title,
                    "category": gym_class.category.name,
                    "instructor": gym_class.instructor.name,
                    "start_time": gym_class.start_time.isoformat(),
                    "available_spots": available,
                    "capacity": gym_class.capacity,
                }
            )
    return result


def get_classes_by_period(
    db: Session,
    category: str | None = None,
    instructor: str | None = None,
    date: str | None = None,
    period: str | None = None,
) -> list[dict]:
    """Lista todas as aulas (com ou sem vaga) de uma modalidade/professor em uma data/período."""
    category_id = _resolve_category_id(db, category)
    instructor_id = _resolve_instructor_id(db, instructor)
    day = _resolve_day(date)
    start = day
    end = day + timedelta(days=7 if date is None and period is None else 1)

    if period in PERIOD_RANGES:
        hour_start, hour_end = PERIOD_RANGES[period]
        start = day.replace(hour=hour_start)
        end = day.replace(hour=hour_end)

    classes = list_classes(db, category_id=category_id, start_after=start, start_before=end)
    if instructor_id is not None:
        classes = [c for c in classes if c.instructor_id == instructor_id]

    return [
        {
            "class_id": c.id,
            "title": c.title,
            "category": c.category.name,
            "instructor": c.instructor.name,
            "start_time": c.start_time.isoformat(),
            "capacity": c.capacity,
            "booked_count": count_active_bookings(db, c.id),
        }
        for c in classes
    ]


def get_user_bookings(db: Session, user_id: int, only_upcoming: bool = True) -> list[dict]:
    """Retorna as reservas (próximas ou histórico) de um aluno específico."""
    bookings = list_by_user(db, user_id, status=BookingStatus.CONFIRMED if only_upcoming else None)
    result = []
    for booking in bookings:
        gym_class = booking.gym_class
        if only_upcoming and gym_class.start_time < _now():
            continue
        result.append(
            {
                "booking_id": booking.id,
                "status": booking.status.value,
                "class_title": gym_class.title,
                "category": gym_class.category.name,
                "start_time": gym_class.start_time.isoformat(),
            }
        )
    return result


def get_class_occupancy(db: Session, class_id: int) -> dict | None:
    """Retorna a ocupação atual (vagas ocupadas/total) de uma aula específica."""
    from app.repositories.class_repository import get_by_id

    gym_class = get_by_id(db, class_id)
    if gym_class is None:
        return None
    booked = count_active_bookings(db, gym_class.id)
    return {
        "class_id": gym_class.id,
        "title": gym_class.title,
        "start_time": gym_class.start_time.isoformat(),
        "capacity": gym_class.capacity,
        "booked_count": booked,
        "available_spots": gym_class.capacity - booked,
        "occupancy_rate": round(booked / gym_class.capacity, 2) if gym_class.capacity else 0,
    }


def get_quietest_times(db: Session, limit: int = 5) -> list[dict]:
    """Retorna os horários (dia da semana + hora) historicamente menos concorridos."""
    return get_quietest_slots(db, limit=limit)


TOOL_REGISTRY = {
    "get_available_classes": get_available_classes,
    "get_classes_by_period": get_classes_by_period,
    "get_user_bookings": get_user_bookings,
    "get_class_occupancy": get_class_occupancy,
    "get_quietest_times": get_quietest_times,
}


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_available_classes",
            "description": "Lista aulas futuras que ainda têm vagas disponíveis, podendo filtrar por modalidade, professor, data e período do dia.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "Nome da modalidade, ex: funcional, yoga, spinning, musculação"},
                    "instructor": {"type": "string", "description": "Nome (ou parte do nome) do professor, ex: Carla, Bruno Lima"},
                    "date": {"type": "string", "description": "'today', 'tomorrow' ou data ISO (YYYY-MM-DD)"},
                    "period": {"type": "string", "enum": ["morning", "afternoon", "evening"], "description": "Período do dia"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_classes_by_period",
            "description": "Lista todas as aulas (com ou sem vaga) de uma modalidade/professor em uma data/período, útil para perguntas como 'quais aulas de funcional existem esta semana' ou 'que horas a Carla dá aula hoje'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string"},
                    "instructor": {"type": "string", "description": "Nome (ou parte do nome) do professor"},
                    "date": {"type": "string"},
                    "period": {"type": "string", "enum": ["morning", "afternoon", "evening"]},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_bookings",
            "description": "Retorna as reservas do aluno autenticado (próximas aulas ou histórico completo).",
            "parameters": {
                "type": "object",
                "properties": {
                    "only_upcoming": {"type": "boolean", "description": "Se true, retorna apenas próximas aulas; se false, retorna o histórico completo"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_class_occupancy",
            "description": "Retorna quantas vagas estão ocupadas e disponíveis em uma aula específica.",
            "parameters": {
                "type": "object",
                "properties": {"class_id": {"type": "integer"}},
                "required": ["class_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_quietest_times",
            "description": "Retorna os horários (dia da semana + hora) historicamente com menor ocupação média, úteis para recomendar o melhor horário para treinar.",
            "parameters": {
                "type": "object",
                "properties": {"limit": {"type": "integer", "description": "Quantidade de horários a retornar"}},
            },
        },
    },
]
