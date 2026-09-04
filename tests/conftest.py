from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.category import Category
from app.models.gym_class import GymClass
from app.models.instructor import Instructor

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def category(db_session):
    cat = Category(name="Funcional", description="Treino funcional")
    db_session.add(cat)
    db_session.commit()
    db_session.refresh(cat)
    return cat


@pytest.fixture()
def instructor(db_session):
    ins = Instructor(name="Bruno Lima", email="bruno@gymflow.com", specialty="Funcional")
    db_session.add(ins)
    db_session.commit()
    db_session.refresh(ins)
    return ins


@pytest.fixture()
def gym_class(db_session, category, instructor):
    start = datetime.now() + timedelta(days=1)
    gc = GymClass(
        title="Funcional com Bruno",
        category_id=category.id,
        instructor_id=instructor.id,
        start_time=start,
        end_time=start + timedelta(hours=1),
        capacity=2,
    )
    db_session.add(gc)
    db_session.commit()
    db_session.refresh(gc)
    return gc


def register_and_login(client, name="Aluno Teste", email="aluno@teste.com", password="senha123"):
    client.post("/auth/register", json={"name": name, "email": email, "password": password})
    response = client.post("/auth/login", json={"email": email, "password": password})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def make_admin(db_session, email="aluno@teste.com"):
    from app.models.user import User, UserRole

    user = db_session.query(User).filter(User.email == email).first()
    user.role = UserRole.ADMIN
    db_session.commit()
    return user
