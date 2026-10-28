from __future__ import annotations

import pytest
from fastapi import HTTPException

from portal.backend.auth import _claims


def test_missing_bearer_token_is_rejected() -> None:
    with pytest.raises(HTTPException) as error:
        _claims(None)

    assert error.value.status_code == 401


def test_authentication_configuration_is_required(monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi.security import HTTPAuthorizationCredentials

    monkeypatch.delenv("OIDC_ISSUER", raising=False)
    monkeypatch.delenv("OIDC_AUDIENCE", raising=False)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="not-a-token")

    with pytest.raises(HTTPException) as error:
        _claims(credentials)

    assert error.value.status_code == 503
