def test_register_and_login(client):
    register_response = client.post(
        "/auth/register",
        json={"name": "Aluno Teste", "email": "aluno@teste.com", "password": "senha123"},
    )
    assert register_response.status_code == 201
    assert register_response.json()["email"] == "aluno@teste.com"

    login_response = client.post("/auth/login", json={"email": "aluno@teste.com", "password": "senha123"})
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()


def test_register_duplicate_email_fails(client):
    payload = {"name": "Aluno Teste", "email": "aluno@teste.com", "password": "senha123"}
    client.post("/auth/register", json=payload)
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 400


def test_login_with_wrong_password_fails(client):
    client.post("/auth/register", json={"name": "Aluno Teste", "email": "aluno@teste.com", "password": "senha123"})
    response = client.post("/auth/login", json={"email": "aluno@teste.com", "password": "errada"})
    assert response.status_code == 401


def test_access_protected_route_without_token_fails(client):
    response = client.get("/users/me")
    assert response.status_code == 401
