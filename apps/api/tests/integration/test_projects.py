from httpx import AsyncClient

from tests.integration.helpers import create_org_and_workspace, register_user


async def test_create_and_get_project(client: AsyncClient) -> None:
    admin = await register_user(client, "admin@example.com")
    _, workspace_id = await create_org_and_workspace(client, admin["headers"])

    create_response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/projects",
        json={"key": "eng", "name": "Engineering", "description": "Core eng project"},
        headers=admin["headers"],
    )
    assert create_response.status_code == 201, create_response.text
    project = create_response.json()["data"]
    assert project["key"] == "ENG"  # normalized to uppercase
    assert project["status"] == "active"
    assert project["progress"] == 0

    get_response = await client.get(f"/api/v1/projects/{project['id']}", headers=admin["headers"])
    assert get_response.status_code == 200
    assert get_response.json()["data"]["name"] == "Engineering"


async def test_duplicate_project_key_conflicts(client: AsyncClient) -> None:
    admin = await register_user(client, "admin@example.com")
    _, workspace_id = await create_org_and_workspace(client, admin["headers"])

    await client.post(
        f"/api/v1/workspaces/{workspace_id}/projects",
        json={"key": "ENG", "name": "Engineering"},
        headers=admin["headers"],
    )
    dup_response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/projects",
        json={"key": "ENG", "name": "Another"},
        headers=admin["headers"],
    )
    assert dup_response.status_code == 409


async def test_non_member_cannot_access_project(client: AsyncClient) -> None:
    admin = await register_user(client, "admin@example.com")
    outsider = await register_user(client, "outsider@example.com")
    _, workspace_id = await create_org_and_workspace(client, admin["headers"])
    project_response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/projects",
        json={"key": "ENG", "name": "Engineering"},
        headers=admin["headers"],
    )
    project_id = project_response.json()["data"]["id"]

    response = await client.get(f"/api/v1/projects/{project_id}", headers=outsider["headers"])
    assert response.status_code == 403


async def test_update_and_archive_project(client: AsyncClient) -> None:
    admin = await register_user(client, "admin@example.com")
    _, workspace_id = await create_org_and_workspace(client, admin["headers"])
    project_response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/projects",
        json={"key": "ENG", "name": "Engineering"},
        headers=admin["headers"],
    )
    project_id = project_response.json()["data"]["id"]

    update_response = await client.patch(
        f"/api/v1/projects/{project_id}", json={"name": "Renamed"}, headers=admin["headers"]
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["name"] == "Renamed"

    archive_response = await client.delete(
        f"/api/v1/projects/{project_id}", headers=admin["headers"]
    )
    assert archive_response.status_code == 200
    assert archive_response.json()["data"]["status"] == "archived"
