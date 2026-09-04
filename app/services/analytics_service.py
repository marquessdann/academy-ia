from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.booking import Booking, BookingStatus
from app.models.gym_class import GymClass
from app.repositories.class_repository import list_classes

DAY_NAMES_PT = [
    "Segunda-feira",
    "Terça-feira",
    "Quarta-feira",
    "Quinta-feira",
    "Sexta-feira",
    "Sábado",
    "Domingo",
]


def _booked_count(gym_class: GymClass) -> int:
    return sum(1 for b in gym_class.bookings if b.status == BookingStatus.CONFIRMED)


def get_occupancy_report(db: Session) -> list[dict]:
    """Taxa de ocupação de cada aula cadastrada (usado pela rota /analytics/occupancy)."""
    classes = list_classes(db)
    report = []
    for gym_class in classes:
        booked = _booked_count(gym_class)
        rate = round(booked / gym_class.capacity, 2) if gym_class.capacity else 0.0
        report.append(
            {
                "class_id": gym_class.id,
                "title": gym_class.title,
                "start_time": gym_class.start_time,
                "capacity": gym_class.capacity,
                "booked_count": booked,
                "occupancy_rate": rate,
            }
        )
    return report


def get_quietest_slots(db: Session, limit: int = 5) -> list[dict]:
    """Agrupa aulas por dia da semana + hora e calcula a ocupação média de cada slot.

    Quanto menor a ocupação média, mais "vazio" costuma estar aquele horário.
    """
    classes = list_classes(db)

    buckets: dict[tuple[int, int], list[float]] = defaultdict(list)
    for gym_class in classes:
        if gym_class.capacity == 0:
            continue
        booked = _booked_count(gym_class)
        rate = booked / gym_class.capacity
        key = (gym_class.start_time.weekday(), gym_class.start_time.hour)
        buckets[key].append(rate)

    slots = []
    for (day_of_week, hour), rates in buckets.items():
        slots.append(
            {
                "day_of_week": day_of_week,
                "day_name": DAY_NAMES_PT[day_of_week],
                "hour": hour,
                "average_occupancy_rate": round(sum(rates) / len(rates), 2),
                "sample_size": len(rates),
            }
        )

    slots.sort(key=lambda slot: slot["average_occupancy_rate"])
    return slots[:limit]
