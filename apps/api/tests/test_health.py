from fastapi.testclient import TestClient

from app.core.config import settings


def test_health_check_returns_true(client: TestClient) -> None:
    r = client.get(f"{settings.API_V1_STR}/utils/health-check/")
    assert r.status_code == 200
    assert r.json() is True


def test_openapi_lists_health_check_path(client: TestClient) -> None:
    r = client.get(f"{settings.API_V1_STR}/openapi.json")
    assert r.status_code == 200
    health = f"{settings.API_V1_STR}/utils/health-check/"
    assert health in r.json().get("paths", {})
