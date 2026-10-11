"""Application-level tests: imports, startup, and health."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "NoteNest API"


def test_openapi_documentation_available(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/health" in response.json()["paths"]


def test_cors_allows_configured_dev_origin(client: TestClient) -> None:
    response = client.get(
        "/health", headers={"Origin": "http://localhost:5173"}
    )

    assert (
        response.headers.get("access-control-allow-origin")
        == "http://localhost:5173"
    )
