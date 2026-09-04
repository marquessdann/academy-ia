from tests.conftest import make_admin, register_and_login


def test_list_classes_is_public(client, gym_class):
    response = client.get("/classes")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["available_spots"] == gym_class.capacity


def test_get_single_class(client, gym_class):
    response = client.get(f"/classes/{gym_class.id}")
    assert response.status_code == 200
    assert response.json()["id"] == gym_class.id


def test_get_nonexistent_class_returns_404(client):
    response = client.get("/classes/999")
    assert response.status_code == 404


def test_only_admin_can_create_class(client, db_session, category, instructor):
    headers = register_and_login(client)
    payload = {
        "title": "Yoga da manhã",
        "category_id": category.id,
        "instructor_id": instructor.id,
        "start_time": "2030-01-01T07:00:00",
        "end_time": "2030-01-01T08:00:00",
        "capacity": 10,
    }

    forbidden_response = client.post("/classes", json=payload, headers=headers)
    assert forbidden_response.status_code == 403

    make_admin(db_session)
    admin_headers = register_and_login(client, email="aluno@teste.com", password="senha123")
    allowed_response = client.post("/classes", json=payload, headers=admin_headers)
    assert allowed_response.status_code == 201
