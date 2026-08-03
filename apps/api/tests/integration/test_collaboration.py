from httpx import AsyncClient

from tests.integration.helpers import create_org_and_workspace, create_project, register_user


async def _setup_work_item(client: AsyncClient) -> tuple[dict, str]:
    admin = await register_user(client, "admin@example.com")
    _, workspace_id = await create_org_and_workspace(client, admin["headers"])
    project_id = await create_project(client, admin["headers"], workspace_id)
    response = await client.post(
        f"/api/v1/projects/{project_id}/work-items",
        json={"type": "task", "title": "A task"},
        headers=admin["headers"],
    )
    return admin, response.json()["data"]["id"]


async def test_comment_lifecycle(client: AsyncClient) -> None:
    admin, work_item_id = await _setup_work_item(client)

    empty_response = await client.get(
        f"/api/v1/work-items/{work_item_id}/comments", headers=admin["headers"]
    )
    assert empty_response.json()["data"] == []

    add_response = await client.post(
        f"/api/v1/work-items/{work_item_id}/comments",
        json={"body": "Looks good to me"},
        headers=admin["headers"],
    )
    assert add_response.status_code == 201
    comment = add_response.json()["data"]
    assert comment["body"] == "Looks good to me"
    assert comment["author_id"] == admin["user_id"]

    list_response = await client.get(
        f"/api/v1/work-items/{work_item_id}/comments", headers=admin["headers"]
    )
    assert len(list_response.json()["data"]) == 1


async def test_empty_comment_rejected(client: AsyncClient) -> None:
    admin, work_item_id = await _setup_work_item(client)
    response = await client.post(
        f"/api/v1/work-items/{work_item_id}/comments",
        json={"body": "   "},
        headers=admin["headers"],
    )
    assert response.status_code == 422


async def test_attachment_lifecycle(client: AsyncClient) -> None:
    admin, work_item_id = await _setup_work_item(client)

    files = {"file": ("notes.txt", b"hello world", "text/plain")}
    upload_response = await client.post(
        f"/api/v1/work-items/{work_item_id}/attachments",
        files=files,
        headers=admin["headers"],
    )
    assert upload_response.status_code == 201, upload_response.text
    attachment = upload_response.json()["data"]
    assert attachment["file_name"] == "notes.txt"
    assert attachment["file_size_bytes"] == len(b"hello world")
    assert attachment["mime_type"] == "text/plain"

    list_response = await client.get(
        f"/api/v1/work-items/{work_item_id}/attachments", headers=admin["headers"]
    )
    assert len(list_response.json()["data"]) == 1


async def test_comments_require_workspace_membership(client: AsyncClient) -> None:
    admin, work_item_id = await _setup_work_item(client)
    outsider = await register_user(client, "outsider@example.com")

    response = await client.get(
        f"/api/v1/work-items/{work_item_id}/comments", headers=outsider["headers"]
    )
    assert response.status_code == 403
