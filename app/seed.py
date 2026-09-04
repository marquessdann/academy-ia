"""Popula o banco com dados de demonstração (modalidades, professores, grade
horária, aulas e algumas reservas), útil para testar a API e o frontend logo
após clonar o projeto.

Uso: python -m app.seed
"""

import random
from datetime import datetime, timedelta, time

from app.auth.security import hash_password
from app.database import Base, SessionLocal, engine
from app.models.booking import Booking, BookingStatus
from app.models.category import Category
from app.models.gym_class import GymClass
from app.models.gym_schedule import GymSchedule
from app.models.instructor import Instructor
from app.models.user import User, UserRole

CATEGORIES = [
    ("Musculação", "Treino de força com pesos livres e máquinas"),
    ("Funcional", "Treino funcional em alta intensidade"),
    ("Spinning", "Aula de ciclismo indoor com música"),
    ("Yoga", "Alongamento, respiração e equilíbrio"),
]

INSTRUCTORS = [
    ("Carla Souza", "carla.souza@gymflow.com", "Musculação"),
    ("Bruno Lima", "bruno.lima@gymflow.com", "Funcional"),
    ("Fernanda Alves", "fernanda.alves@gymflow.com", "Spinning"),
    ("Rafael Costa", "rafael.costa@gymflow.com", "Yoga"),
]

DEMO_STUDENTS = [
    ("Ana Paula", "ana.paula@example.com"),
    ("João Pedro", "joao.pedro@example.com"),
    ("Mariana Dias", "mariana.dias@example.com"),
    ("Lucas Martins", "lucas.martins@example.com"),
    ("Beatriz Rocha", "beatriz.rocha@example.com"),
]

SCHEDULE_TEMPLATE = [
    # (day_of_week, start_hour, end_hour, category_index)
    (0, 7, 8, 0), (0, 18, 19, 1), (0, 19, 20, 2),
    (1, 7, 8, 1), (1, 12, 13, 3), (1, 19, 20, 0),
    (2, 7, 8, 2), (2, 18, 19, 1), (2, 19, 20, 3),
    (3, 7, 8, 1), (3, 12, 13, 0), (3, 19, 20, 2),
    (4, 7, 8, 3), (4, 18, 19, 0), (4, 19, 20, 1),
    (5, 9, 10, 2), (5, 10, 11, 3),
]


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        if db.query(Category).count() > 0:
            print("Banco já contém dados. Seed abortado para evitar duplicidade.")
            return

        categories = [Category(name=name, description=desc) for name, desc in CATEGORIES]
        db.add_all(categories)
        db.commit()

        instructors = []
        for name, email, specialty in INSTRUCTORS:
            instructor = Instructor(name=name, email=email, specialty=specialty, bio=f"Especialista em {specialty}.")
            instructors.append(instructor)
        db.add_all(instructors)
        db.commit()

        admin = User(name="Admin GymFlow", email="admin@gymflow.com", hashed_password=hash_password("admin123"), role=UserRole.ADMIN)
        db.add(admin)

        students = []
        for name, email in DEMO_STUDENTS:
            student = User(name=name, email=email, hashed_password=hash_password("aluno123"), role=UserRole.STUDENT)
            students.append(student)
        db.add_all(students)
        db.commit()

        schedules = []
        for day_of_week, start_hour, end_hour, category_idx in SCHEDULE_TEMPLATE:
            schedule = GymSchedule(
                category_id=categories[category_idx].id,
                instructor_id=instructors[category_idx].id,
                day_of_week=day_of_week,
                start_time=time(hour=start_hour),
                end_time=time(hour=end_hour),
                capacity=random.choice([10, 12, 15, 20]),
            )
            schedules.append(schedule)
        db.add_all(schedules)
        db.commit()

        today = datetime.now().replace(minute=0, second=0, microsecond=0)
        monday = today - timedelta(days=today.weekday())

        gym_classes = []
        for week_offset in (-1, 0, 1):
            for schedule in schedules:
                class_date = monday + timedelta(days=schedule.day_of_week, weeks=week_offset)
                start_time = class_date.replace(hour=schedule.start_time.hour, minute=0)
                end_time = class_date.replace(hour=schedule.end_time.hour, minute=0)
                category = next(c for c in categories if c.id == schedule.category_id)
                gym_class = GymClass(
                    title=f"{category.name} com {next(i for i in instructors if i.id == schedule.instructor_id).name}",
                    category_id=schedule.category_id,
                    instructor_id=schedule.instructor_id,
                    schedule_id=schedule.id,
                    start_time=start_time,
                    end_time=end_time,
                    capacity=schedule.capacity,
                )
                gym_classes.append(gym_class)
        db.add_all(gym_classes)
        db.commit()

        # Cria reservas aleatórias (mais concentradas em horários de manhã/noite
        # de dias úteis, para gerar dados de ocupação realistas para a IA).
        for gym_class in gym_classes:
            is_evening = gym_class.start_time.hour >= 18
            is_weekday = gym_class.start_time.weekday() < 5
            base_fill_ratio = 0.75 if (is_evening and is_weekday) else 0.3
            n_bookings = min(gym_class.capacity, round(gym_class.capacity * base_fill_ratio))
            chosen_students = random.sample(students, k=min(n_bookings, len(students)))
            for student in chosen_students:
                db.add(Booking(user_id=student.id, class_id=gym_class.id, status=BookingStatus.CONFIRMED))
        db.commit()

        print("Seed concluído com sucesso!")
        print("Login admin: admin@gymflow.com / admin123")
        print("Login aluno: ana.paula@example.com / aluno123")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
