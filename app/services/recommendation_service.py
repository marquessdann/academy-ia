from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.repositories.class_repository import list_classes
from app.services.analytics_service import get_quietest_slots


def recommend_best_times(db: Session, category_id: int | None = None, limit: int = 3) -> list[dict]:
    """Recomenda horários com histórico de baixa ocupação e que ainda têm aulas futuras.

    Regra simples baseada em dados (sem ML): calcula a ocupação média por
    combinação de dia da semana + hora (get_quietest_slots) e casa esse
    resultado com as próximas aulas futuras que caem nesses horários.
    """
    quietest_slots = get_quietest_slots(db, limit=20)
    slot_rank = {(slot["day_of_week"], slot["hour"]): slot for slot in quietest_slots}

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    upcoming_classes = [c for c in list_classes(db, category_id=category_id) if c.start_time >= now]

    recommendations = []
    for gym_class in upcoming_classes:
        key = (gym_class.start_time.weekday(), gym_class.start_time.hour)
        slot_info = slot_rank.get(key)
        if slot_info is None:
            continue
        recommendations.append(
            {
                "class_id": gym_class.id,
                "title": gym_class.title,
                "start_time": gym_class.start_time,
                "average_occupancy_rate": slot_info["average_occupancy_rate"],
                "reason": (
                    f"Historicamente, aulas às {gym_class.start_time.strftime('%H:%M')} de "
                    f"{slot_info['day_name']} têm ocupação média de "
                    f"{slot_info['average_occupancy_rate'] * 100:.0f}%."
                ),
            }
        )

    recommendations.sort(key=lambda r: r["average_occupancy_rate"])
    return recommendations[:limit]
