"""JWT edge-case coverage for protected routes (expiration, malformed, bad signature, unknown principal)."""

import uuid
from datetime import UTC, datetime, timedelta

import jwt
from fastapi.testclient import TestClient
from sqlmodel import Session

from app import crud
from app.core import security
from app.core.config import settings
from app.models import UserCreate
from tests.utils.utils import random_email, random_lower_string


def _post_test_token(client: TestClient, headers: dict[str, str]):
    return client.post(
        f"{settings.API_V1_STR}/login/test-token",
        headers=headers,
    )


def test_test_token_without_authorization_returns_401(client: TestClient) -> None:
    r = client.post(f"{settings.API_V1_STR}/login/test-token")
    assert r.status_code == 401
    assert r.json()["detail"] == "Not authenticated"


def test_access_token_expired_returns_403(client: TestClient) -> None:
    token = security.create_access_token(
        uuid.uuid4(),
        expires_delta=timedelta(minutes=-10),
    )
    r = _post_test_token(client, {"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
    assert r.json()["detail"] == "Could not validate credentials"


def test_access_token_malformed_returns_403(client: TestClient) -> None:
    r = _post_test_token(client, {"Authorization": "Bearer not-a-valid-jwt"})
    assert r.status_code == 403
    assert r.json()["detail"] == "Could not validate credentials"


def test_access_token_wrong_signing_key_returns_403(client: TestClient) -> None:
    token = jwt.encode(
        {
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "sub": str(uuid.uuid4()),
        },
        "definitely-not-the-app-secret",
        algorithm=security.ALGORITHM,
    )
    r = _post_test_token(client, {"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
    assert r.json()["detail"] == "Could not validate credentials"


def test_access_token_wrong_algorithm_returns_403(client: TestClient) -> None:
    """JWT must match ALGORITHM (`HS256`); wrong alg fails jwt.decode."""
    token = jwt.encode(
        {
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "sub": str(uuid.uuid4()),
        },
        settings.SECRET_KEY,
        algorithm="HS384",
    )
    r = _post_test_token(client, {"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
    assert r.json()["detail"] == "Could not validate credentials"


def test_access_token_invalid_subject_claim_returns_403(client: TestClient) -> None:
    """`sub` must fit `TokenPayload`; bad shapes fail validation before DB lookup."""
    token = jwt.encode(
        {
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "sub": ["not-a-valid-subject-claim"],
        },
        settings.SECRET_KEY,
        algorithm=security.ALGORITHM,
    )
    r = _post_test_token(client, {"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
    assert r.json()["detail"] == "Could not validate credentials"


def test_access_token_unknown_user_returns_404(client: TestClient) -> None:
    missing_id = uuid.uuid4()
    token = security.create_access_token(
        missing_id,
        expires_delta=timedelta(minutes=30),
    )
    r = _post_test_token(client, {"Authorization": f"Bearer {token}"})
    assert r.status_code == 404
    assert r.json()["detail"] == "User not found"


def test_access_token_without_sub_claim_returns_404(client: TestClient) -> None:
    """JWT decodes but `TokenPayload.sub` stays None → no principal to load."""
    token = jwt.encode(
        {
            "exp": datetime.now(UTC) + timedelta(hours=1),
        },
        settings.SECRET_KEY,
        algorithm=security.ALGORITHM,
    )
    r = _post_test_token(client, {"Authorization": f"Bearer {token}"})
    assert r.status_code == 404
    assert r.json()["detail"] == "User not found"


def test_access_token_null_sub_returns_403(client: TestClient) -> None:
    """PyJWT rejects `sub: null` during decode (`InvalidSubjectError`)."""
    token = jwt.encode(
        {
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "sub": None,
        },
        settings.SECRET_KEY,
        algorithm=security.ALGORITHM,
    )
    r = _post_test_token(client, {"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
    assert r.json()["detail"] == "Could not validate credentials"


def test_access_token_empty_subject_returns_403(client: TestClient) -> None:
    """`sub` typed as UUID; empty string fails pydantic coercion → 403 before DB."""
    token = jwt.encode(
        {
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "sub": "",
        },
        settings.SECRET_KEY,
        algorithm=security.ALGORITHM,
    )
    r = _post_test_token(client, {"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
    assert r.json()["detail"] == "Could not validate credentials"


def test_access_token_inactive_user_returns_400(
    client: TestClient, db: Session
) -> None:
    user_create = UserCreate(
        email=random_email(),
        full_name="Inactive User",
        password=random_lower_string(),
        is_active=False,
        is_superuser=False,
    )
    user = crud.create_user(session=db, user_create=user_create)
    token = security.create_access_token(
        user.id,
        expires_delta=timedelta(minutes=30),
    )
    r = _post_test_token(client, {"Authorization": f"Bearer {token}"})
    assert r.status_code == 400
    assert r.json()["detail"] == "Inactive user"
