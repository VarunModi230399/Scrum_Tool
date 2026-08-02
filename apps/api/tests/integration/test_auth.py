from httpx import AsyncClient


async def _register(client: AsyncClient, email: str = "ada@example.com") -> dict:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "correct-horse-1", "full_name": "Ada Lovelace"},
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


async def test_register_creates_user_and_returns_tokens(client: AsyncClient) -> None:
    data = await _register(client)
    assert data["user"]["email"] == "ada@example.com"
    assert data["access_token"]
    assert data["refresh_token"]


async def test_register_duplicate_email_conflicts(client: AsyncClient) -> None:
    await _register(client)
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "ada@example.com", "password": "another-pass-1", "full_name": "Ada Two"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


async def test_login_success(client: AsyncClient) -> None:
    await _register(client)
    response = await client.post(
        "/api/v1/auth/login", json={"email": "ada@example.com", "password": "correct-horse-1"}
    )
    assert response.status_code == 200
    assert response.json()["data"]["access_token"]


async def test_login_wrong_password_is_rejected(client: AsyncClient) -> None:
    await _register(client)
    response = await client.post(
        "/api/v1/auth/login", json={"email": "ada@example.com", "password": "wrong-password"}
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


async def test_me_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


async def test_me_returns_current_user(client: AsyncClient) -> None:
    data = await _register(client)
    response = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {data['access_token']}"}
    )
    assert response.status_code == 200
    assert response.json()["data"]["email"] == "ada@example.com"


async def test_refresh_rotates_token_and_invalidates_the_old_one(client: AsyncClient) -> None:
    data = await _register(client)
    old_refresh = data["refresh_token"]

    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert response.status_code == 200
    new_tokens = response.json()["data"]
    assert new_tokens["refresh_token"] != old_refresh

    reuse_response = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert reuse_response.status_code == 401


async def test_logout_revokes_refresh_token(client: AsyncClient) -> None:
    data = await _register(client)
    logout_response = await client.post(
        "/api/v1/auth/logout", json={"refresh_token": data["refresh_token"]}
    )
    assert logout_response.status_code == 204

    refresh_response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": data["refresh_token"]}
    )
    assert refresh_response.status_code == 401
