"""Bearer Authorization hardening on protected routes.

Multi-tenant APIs depend on parsing a Bearer token before tenant context middleware
can run. Until tenant middleware lands in-app, these tests assert that malformed or
non-Bearer schemes are rejected consistently on authenticated endpoints.
"""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api import deps as deps_module
from app.core.config import settings


def test_malformed_bearer_missing_token_rejected(client: TestClient) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/login/test-token",
        headers={"Authorization": "Bearer"},
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "Could not validate credentials"


def test_malformed_bearer_whitespace_only_token_rejected(
    client: TestClient,
) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/login/test-token",
        headers={"Authorization": "Bearer       "},
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "Could not validate credentials"


def test_non_bearer_scheme_rejected(client: TestClient) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/login/test-token",
        headers={"Authorization": "Basic dGVzdA=="},
    )
    assert r.status_code == 401


def test_users_me_rejects_malformed_bearer_when_multi_tenancy_enabled(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Same OAuth2 parsing path as `/login/test-token` on another protected router."""

    multitenant_settings = MagicMock(wraps=settings)
    multitenant_settings.MULTI_TENANCY_ENABLED = True
    monkeypatch.setattr(deps_module, "settings", multitenant_settings)

    r = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": "Bearer"},
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "Could not validate credentials"


def test_when_multi_tenancy_enabled_malformed_bearer_rejected(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Future tenant middleware stacks after OAuth parsing; Bearer must stay strict."""

    multitenant_settings = MagicMock(wraps=settings)
    multitenant_settings.MULTI_TENANCY_ENABLED = True
    monkeypatch.setattr(deps_module, "settings", multitenant_settings)

    r = client.post(
        f"{settings.API_V1_STR}/login/test-token",
        headers={"Authorization": "Bearer not-a-real-jwt"},
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "Could not validate credentials"

    missing = client.post(
        f"{settings.API_V1_STR}/login/test-token",
        headers={"Authorization": "Bearer"},
    )
    assert missing.status_code == 403
    assert missing.json()["detail"] == "Could not validate credentials"
