from datetime import datetime, timedelta

from app.models.booking import Booking, BookingStatus
from app.models.gym_class import GymClass
from app.models.user import User, UserRole
from app.services import analytics_service, recommendation_service


def _make_student(db_session, email):
    user = User(name="Aluno", email=email, hashed_password="x", role=UserRole.STUDENT)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_quietest_slots_ranks_lower_occupancy_first(db_session, category, instructor):
    crowded_start = datetime.now() + timedelta(days=2, hours=1)
    crowded = GymClass(
        title="Aula cheia",
        category_id=category.id,
        instructor_id=instructor.id,
        start_time=crowded_start,
        end_time=crowded_start + timedelta(hours=1),
        capacity=2,
    )
    empty_start = datetime.now() + timedelta(days=3, hours=1)
    empty = GymClass(
        title="Aula vazia",
        category_id=category.id,
        instructor_id=instructor.id,
        start_time=empty_start,
        end_time=empty_start + timedelta(hours=1),
        capacity=10,
    )
    db_session.add_all([crowded, empty])
    db_session.commit()

    student = _make_student(db_session, "aluno1@teste.com")
    db_session.add(Booking(user_id=student.id, class_id=crowded.id, status=BookingStatus.CONFIRMED))
    db_session.commit()

    slots = analytics_service.get_quietest_slots(db_session)
    quietest = slots[0]
    assert quietest["hour"] == empty_start.hour
    assert quietest["average_occupancy_rate"] == 0.0


def test_recommend_best_times_returns_upcoming_classes(db_session, category, instructor):
    start = datetime.now() + timedelta(days=1, hours=2)
    gym_class = GymClass(
        title="Aula recomendada",
        category_id=category.id,
        instructor_id=instructor.id,
        start_time=start,
        end_time=start + timedelta(hours=1),
        capacity=10,
    )
    db_session.add(gym_class)
    db_session.commit()

    recommendations = recommendation_service.recommend_best_times(db_session)
    assert len(recommendations) == 1
    assert recommendations[0]["class_id"] == gym_class.id
