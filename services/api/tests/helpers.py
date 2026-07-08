from fastapi.testclient import TestClient


def auth_header(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def login(client: TestClient, email: str, password: str) -> dict:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()


def register(
    client: TestClient,
    *,
    email: str,
    password: str,
    role: str,
    invite_code: str,
) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "role": role,
            "invite_code": invite_code,
        },
    )
    assert response.status_code == 201
    return response.json()
