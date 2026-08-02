from fastapi.testclient import TestClient


def test_liveness(sync_client: TestClient) -> None:
    response = sync_client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
