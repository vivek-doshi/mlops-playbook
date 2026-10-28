"""OIDC authentication and role checks for the self-service portal."""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Any

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

logger = logging.getLogger(__name__)
_bearer = HTTPBearer(auto_error=False)


@lru_cache(maxsize=1)
def _jwks_client() -> PyJWKClient:
    url = os.environ.get("OIDC_JWKS_URL", "")
    if not url:
        raise RuntimeError("OIDC_JWKS_URL must be configured")
    return PyJWKClient(url)


def _claims(credentials: HTTPAuthorizationCredentials | None) -> dict[str, Any]:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token required")

    issuer = os.environ.get("OIDC_ISSUER", "")
    audience = os.environ.get("OIDC_AUDIENCE", "")
    if not issuer or not audience:
        logger.error("OIDC_ISSUER and OIDC_AUDIENCE must be configured")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Authentication is not configured")

    try:
        signing_key = _jwks_client().get_signing_key_from_jwt(credentials.credentials)
        return jwt.decode(
            credentials.credentials,
            signing_key.key,
            algorithms=["RS256"],
            audience=audience,
            issuer=issuer,
            options={"require": ["exp", "iss", "aud", "sub"]},
        )
    except (jwt.PyJWTError, RuntimeError) as exc:
        logger.warning("OIDC token validation failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token") from exc


def require_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict[str, Any]:
    claims = _claims(credentials)
    request.state.user = claims
    return claims


def require_role(role: str):
    def dependency(claims: dict[str, Any] = Depends(require_user)) -> dict[str, Any]:
        groups = set(claims.get("groups", []))
        configured_group = os.environ.get(f"PORTAL_{role.upper()}_GROUP", "")
        if not configured_group or configured_group not in groups:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"{role} role required")
        return claims

    return dependency
