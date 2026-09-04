from tests.conftest import register_and_login


def test_create_and_list_booking(client, gym_class):
    headers = register_and_login(client)
    response = client.post("/bookings", json={"class_id": gym_class.id}, headers=headers)
    assert response.status_code == 201
    assert response.json()["status"] == "confirmed"

    bookings_response = client.get("/users/me/bookings", headers=headers)
    assert len(bookings_response.json()) == 1


def test_duplicate_booking_is_rejected(client, gym_class):
    headers = register_and_login(client)
    client.post("/bookings", json={"class_id": gym_class.id}, headers=headers)
    response = client.post("/bookings", json={"class_id": gym_class.id}, headers=headers)
    assert response.status_code == 409


def test_booking_fails_when_class_is_full(client, gym_class):
    # gym_class fixture tem capacity=2
    headers_a = register_and_login(client, email="aluno.a@teste.com")
    headers_b = register_and_login(client, email="aluno.b@teste.com")
    headers_c = register_and_login(client, email="aluno.c@teste.com")

    assert client.post("/bookings", json={"class_id": gym_class.id}, headers=headers_a).status_code == 201
    assert client.post("/bookings", json={"class_id": gym_class.id}, headers=headers_b).status_code == 201

    response = client.post("/bookings", json={"class_id": gym_class.id}, headers=headers_c)
    assert response.status_code == 409
    assert "lotada" in response.json()["detail"]


def test_cancel_booking_frees_up_a_spot(client, gym_class):
    headers_a = register_and_login(client, email="aluno.a@teste.com")
    headers_b = register_and_login(client, email="aluno.b@teste.com")
    headers_c = register_and_login(client, email="aluno.c@teste.com")

    booking_a = client.post("/bookings", json={"class_id": gym_class.id}, headers=headers_a).json()
    client.post("/bookings", json={"class_id": gym_class.id}, headers=headers_b)

    cancel_response = client.delete(f"/bookings/{booking_a['id']}", headers=headers_a)
    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "cancelled"

    response = client.post("/bookings", json={"class_id": gym_class.id}, headers=headers_c)
    assert response.status_code == 201


def test_cancel_someone_elses_booking_fails(client, gym_class):
    headers_a = register_and_login(client, email="aluno.a@teste.com")
    headers_b = register_and_login(client, email="aluno.b@teste.com")

    booking_a = client.post("/bookings", json={"class_id": gym_class.id}, headers=headers_a).json()
    response = client.delete(f"/bookings/{booking_a['id']}", headers=headers_b)
    assert response.status_code == 404
