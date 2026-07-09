import hashlib

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
    phone_number: str | None = None,
) -> dict:
    digest = hashlib.sha1(email.encode("utf-8")).hexdigest()[:10]
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "phone_number": phone_number or f"+1555{int(digest, 16) % 10_000_000:07d}",
            "password": password,
            "role": role,
            "verification_code": "123456",
            "terms_accepted": True,
        },
    )
    assert response.status_code == 201
    return response.json()
