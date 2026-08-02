from httpx import AsyncClient


async def register_user(client: AsyncClient, email: str, full_name: str = "Test User") -> dict:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "correct-horse-1", "full_name": full_name},
    )
    assert response.status_code == 201, response.text
    data = response.json()["data"]
    return {
        "user_id": data["user"]["id"],
        "headers": {"Authorization": f"Bearer {data['access_token']}"},
    }


async def create_org_and_workspace(client: AsyncClient, headers: dict) -> tuple[str, str]:
    org_response = await client.post(
        "/api/v1/organizations", json={"name": "Acme Inc"}, headers=headers
    )
    assert org_response.status_code == 201, org_response.text
    org_id = org_response.json()["data"]["id"]

    workspace_response = await client.post(
        f"/api/v1/organizations/{org_id}/workspaces", json={"name": "Engineering"}, headers=headers
    )
    assert workspace_response.status_code == 201, workspace_response.text
    return org_id, workspace_response.json()["data"]["id"]


async def create_project(
    client: AsyncClient, headers: dict, workspace_id: str, key: str = "ENG"
) -> str:
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/projects",
        json={"key": key, "name": "Engineering Project"},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]["id"]
