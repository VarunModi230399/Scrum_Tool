from httpx import AsyncClient

from tests.integration.helpers import create_org_and_workspace, create_project, register_user


async def _setup_project(client: AsyncClient) -> tuple[dict, str]:
    admin = await register_user(client, "admin@example.com")
    _, workspace_id = await create_org_and_workspace(client, admin["headers"])
    project_id = await create_project(client, admin["headers"], workspace_id)
    return admin, project_id


async def _create_work_item(client: AsyncClient, headers: dict, project_id: str, **body) -> dict:
    payload = {"type": "task", "title": "Untitled", **body}
    response = await client.post(
        f"/api/v1/projects/{project_id}/work-items", json=payload, headers=headers
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


async def test_create_work_item_hierarchy(client: AsyncClient) -> None:
    admin, project_id = await _setup_project(client)
    epic = await _create_work_item(
        client, admin["headers"], project_id, type="epic", title="Epic 1"
    )
    story = await _create_work_item(
        client, admin["headers"], project_id, type="story", title="Story 1", parent_id=epic["id"]
    )
    assert story["parent_id"] == epic["id"]
    assert story["depth"] == 1
    assert story["path"] == f"{epic['id']}.{story['id']}"

    children_response = await client.get(
        f"/api/v1/work-items/{epic['id']}/children", headers=admin["headers"]
    )
    assert [c["id"] for c in children_response.json()["data"]] == [story["id"]]

    ancestors_response = await client.get(
        f"/api/v1/work-items/{story['id']}/ancestors", headers=admin["headers"]
    )
    assert [a["id"] for a in ancestors_response.json()["data"]] == [epic["id"]]


async def test_parent_must_be_in_same_project(client: AsyncClient) -> None:
    admin, project_id = await _setup_project(client)
    _, other_workspace_id = await create_org_and_workspace(client, admin["headers"])
    other_project_id = await create_project(client, admin["headers"], other_workspace_id, key="OTH")
    other_epic = await _create_work_item(
        client, admin["headers"], other_project_id, type="epic", title="Other Epic"
    )

    response = await client.post(
        f"/api/v1/projects/{project_id}/work-items",
        json={"type": "story", "title": "Cross-project story", "parent_id": other_epic["id"]},
        headers=admin["headers"],
    )
    assert response.status_code == 422


async def test_leaf_progress_follows_status(client: AsyncClient) -> None:
    admin, project_id = await _setup_project(client)
    task = await _create_work_item(client, admin["headers"], project_id, title="Solo task")
    assert task["progress"] == 0

    response = await client.patch(
        f"/api/v1/work-items/{task['id']}", json={"status": "done"}, headers=admin["headers"]
    )
    assert response.status_code == 200
    assert response.json()["data"]["progress"] == 100


async def test_progress_rolls_up_weighted_by_story_points(client: AsyncClient) -> None:
    admin, project_id = await _setup_project(client)
    epic = await _create_work_item(client, admin["headers"], project_id, type="epic", title="Epic")
    s1 = await _create_work_item(
        client,
        admin["headers"],
        project_id,
        type="story",
        title="S1",
        parent_id=epic["id"],
        story_points=2,
    )
    s2 = await _create_work_item(
        client,
        admin["headers"],
        project_id,
        type="story",
        title="S2",
        parent_id=epic["id"],
        story_points=6,
    )

    async def epic_progress() -> float:
        r = await client.get(f"/api/v1/work-items/{epic['id']}", headers=admin["headers"])
        return r.json()["data"]["progress"]

    assert await epic_progress() == 0

    await client.patch(
        f"/api/v1/work-items/{s1['id']}", json={"status": "done"}, headers=admin["headers"]
    )
    assert await epic_progress() == 25.0  # (2*100 + 6*0) / 8

    await client.patch(
        f"/api/v1/work-items/{s2['id']}", json={"status": "done"}, headers=admin["headers"]
    )
    assert await epic_progress() == 100.0


async def test_progress_override_cascades_effective_value(client: AsyncClient) -> None:
    admin, project_id = await _setup_project(client)
    grandparent = await _create_work_item(
        client, admin["headers"], project_id, type="epic", title="Grandparent"
    )
    parent = await _create_work_item(
        client,
        admin["headers"],
        project_id,
        type="feature",
        title="Parent",
        parent_id=grandparent["id"],
        story_points=1,
    )
    await _create_work_item(
        client,
        admin["headers"],
        project_id,
        type="feature",
        title="Sibling",
        parent_id=grandparent["id"],
        story_points=1,
    )
    await _create_work_item(
        client,
        admin["headers"],
        project_id,
        title="Child A",
        parent_id=parent["id"],
        story_points=1,
    )

    async def get(work_item_id: str) -> dict:
        r = await client.get(f"/api/v1/work-items/{work_item_id}", headers=admin["headers"])
        return r.json()["data"]

    override_response = await client.patch(
        f"/api/v1/work-items/{parent['id']}/progress-override",
        json={"value": 10},
        headers=admin["headers"],
    )
    assert override_response.status_code == 200
    assert override_response.json()["data"]["progress_override"] == 10

    # grandparent's average uses parent's override (10) and sibling's computed progress (0)
    assert (await get(grandparent["id"]))["progress"] == 5.0

    clear_response = await client.patch(
        f"/api/v1/work-items/{parent['id']}/progress-override",
        json={"value": None},
        headers=admin["headers"],
    )
    assert clear_response.json()["data"]["progress_override"] is None
    # parent recomputes from its one child (todo -> 0), grandparent follows
    assert (await get(parent["id"]))["progress"] == 0.0
    assert (await get(grandparent["id"]))["progress"] == 0.0


async def test_move_work_item_reparents_and_updates_path(client: AsyncClient) -> None:
    admin, project_id = await _setup_project(client)
    epic_a = await _create_work_item(client, admin["headers"], project_id, type="epic", title="A")
    epic_b = await _create_work_item(client, admin["headers"], project_id, type="epic", title="B")
    story = await _create_work_item(
        client, admin["headers"], project_id, type="story", title="S", parent_id=epic_a["id"]
    )

    move_response = await client.patch(
        f"/api/v1/work-items/{story['id']}/move",
        json={"new_parent_id": epic_b["id"]},
        headers=admin["headers"],
    )
    assert move_response.status_code == 200
    moved = move_response.json()["data"]
    assert moved["parent_id"] == epic_b["id"]
    assert moved["path"] == f"{epic_b['id']}.{story['id']}"

    a_children = await client.get(
        f"/api/v1/work-items/{epic_a['id']}/children", headers=admin["headers"]
    )
    assert a_children.json()["data"] == []
    b_children = await client.get(
        f"/api/v1/work-items/{epic_b['id']}/children", headers=admin["headers"]
    )
    assert [c["id"] for c in b_children.json()["data"]] == [story["id"]]


async def test_cannot_move_work_item_into_its_own_descendant(client: AsyncClient) -> None:
    admin, project_id = await _setup_project(client)
    epic = await _create_work_item(client, admin["headers"], project_id, type="epic", title="Epic")
    story = await _create_work_item(
        client, admin["headers"], project_id, type="story", title="Story", parent_id=epic["id"]
    )

    response = await client.patch(
        f"/api/v1/work-items/{epic['id']}/move",
        json={"new_parent_id": story["id"]},
        headers=admin["headers"],
    )
    assert response.status_code == 422


async def test_deleting_parent_cascades_to_children(client: AsyncClient) -> None:
    admin, project_id = await _setup_project(client)
    epic = await _create_work_item(client, admin["headers"], project_id, type="epic", title="Epic")
    story = await _create_work_item(
        client, admin["headers"], project_id, type="story", title="Story", parent_id=epic["id"]
    )

    delete_response = await client.delete(
        f"/api/v1/work-items/{epic['id']}", headers=admin["headers"]
    )
    assert delete_response.status_code == 204

    story_response = await client.get(f"/api/v1/work-items/{story['id']}", headers=admin["headers"])
    assert story_response.status_code == 404


async def test_dependency_lifecycle(client: AsyncClient) -> None:
    admin, project_id = await _setup_project(client)
    a = await _create_work_item(client, admin["headers"], project_id, title="A")
    b = await _create_work_item(client, admin["headers"], project_id, title="B")

    self_dep = await client.post(
        f"/api/v1/work-items/{a['id']}/dependencies",
        json={"depends_on_id": a["id"]},
        headers=admin["headers"],
    )
    assert self_dep.status_code == 422

    add_response = await client.post(
        f"/api/v1/work-items/{a['id']}/dependencies",
        json={"depends_on_id": b["id"], "type": "blocks"},
        headers=admin["headers"],
    )
    assert add_response.status_code == 201
    dependency_id = add_response.json()["data"]["id"]

    duplicate_response = await client.post(
        f"/api/v1/work-items/{a['id']}/dependencies",
        json={"depends_on_id": b["id"]},
        headers=admin["headers"],
    )
    assert duplicate_response.status_code == 409

    cycle_response = await client.post(
        f"/api/v1/work-items/{b['id']}/dependencies",
        json={"depends_on_id": a["id"]},
        headers=admin["headers"],
    )
    assert cycle_response.status_code == 422

    list_response = await client.get(
        f"/api/v1/work-items/{a['id']}/dependencies", headers=admin["headers"]
    )
    assert len(list_response.json()["data"]) == 1

    remove_response = await client.delete(
        f"/api/v1/work-items/{a['id']}/dependencies/{dependency_id}", headers=admin["headers"]
    )
    assert remove_response.status_code == 204
