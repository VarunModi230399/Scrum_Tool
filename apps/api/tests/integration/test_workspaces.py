from httpx import AsyncClient


async def _register(client: AsyncClient, email: str, full_name: str) -> dict:
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


async def _create_org_and_workspace(client: AsyncClient, headers: dict) -> tuple[str, str]:
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


async def test_create_organization_and_workspace_flow(client: AsyncClient) -> None:
    admin = await _register(client, "admin@example.com", "Admin User")
    org_id, workspace_id = await _create_org_and_workspace(client, admin["headers"])

    workspaces_response = await client.get(
        f"/api/v1/organizations/{org_id}/workspaces", headers=admin["headers"]
    )
    assert workspaces_response.status_code == 200
    assert len(workspaces_response.json()["data"]) == 1

    workspace_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}", headers=admin["headers"]
    )
    assert workspace_response.status_code == 200

    members_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/members", headers=admin["headers"]
    )
    members = members_response.json()["data"]
    assert len(members) == 1
    assert members[0]["role"] == "admin"


async def test_non_member_cannot_view_workspace_or_organization(client: AsyncClient) -> None:
    admin = await _register(client, "admin@example.com", "Admin User")
    outsider = await _register(client, "outsider@example.com", "Outsider")
    org_id, workspace_id = await _create_org_and_workspace(client, admin["headers"])

    workspace_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}", headers=outsider["headers"]
    )
    assert workspace_response.status_code == 403

    org_response = await client.get(f"/api/v1/organizations/{org_id}", headers=outsider["headers"])
    assert org_response.status_code == 403


async def test_only_admin_can_add_members(client: AsyncClient) -> None:
    admin = await _register(client, "admin@example.com", "Admin User")
    member = await _register(client, "member@example.com", "New Member")
    _, workspace_id = await _create_org_and_workspace(client, admin["headers"])

    forbidden_response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/members",
        json={"user_id": member["user_id"], "role": "developer"},
        headers=member["headers"],
    )
    assert forbidden_response.status_code == 403

    add_response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/members",
        json={"user_id": member["user_id"], "role": "developer"},
        headers=admin["headers"],
    )
    assert add_response.status_code == 201
    assert add_response.json()["data"]["role"] == "developer"

    duplicate_response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/members",
        json={"user_id": member["user_id"], "role": "developer"},
        headers=admin["headers"],
    )
    assert duplicate_response.status_code == 409


async def test_update_and_remove_member(client: AsyncClient) -> None:
    admin = await _register(client, "admin@example.com", "Admin User")
    member = await _register(client, "member@example.com", "New Member")
    _, workspace_id = await _create_org_and_workspace(client, admin["headers"])

    await client.post(
        f"/api/v1/workspaces/{workspace_id}/members",
        json={"user_id": member["user_id"], "role": "developer"},
        headers=admin["headers"],
    )

    update_response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/members/{member['user_id']}",
        json={"role": "scrum_master"},
        headers=admin["headers"],
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["role"] == "scrum_master"

    remove_response = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/members/{member['user_id']}", headers=admin["headers"]
    )
    assert remove_response.status_code == 204

    members_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/members", headers=admin["headers"]
    )
    assert len(members_response.json()["data"]) == 1


async def test_admin_cannot_remove_self(client: AsyncClient) -> None:
    admin = await _register(client, "admin@example.com", "Admin User")
    _, workspace_id = await _create_org_and_workspace(client, admin["headers"])

    response = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/members/{admin['user_id']}", headers=admin["headers"]
    )
    assert response.status_code == 403


async def test_only_admin_can_rename_workspace(client: AsyncClient) -> None:
    admin = await _register(client, "admin@example.com", "Admin User")
    member = await _register(client, "member@example.com", "New Member")
    _, workspace_id = await _create_org_and_workspace(client, admin["headers"])
    await client.post(
        f"/api/v1/workspaces/{workspace_id}/members",
        json={"user_id": member["user_id"], "role": "developer"},
        headers=admin["headers"],
    )

    forbidden_response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}", json={"name": "Renamed"}, headers=member["headers"]
    )
    assert forbidden_response.status_code == 403

    rename_response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}", json={"name": "Renamed"}, headers=admin["headers"]
    )
    assert rename_response.status_code == 200
    assert rename_response.json()["data"]["name"] == "Renamed"
