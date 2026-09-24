from __future__ import annotations
from dataclasses import dataclass
from typing import Callable

import jwt
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.config import settings


bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    subject: str
    tenant_id: str
    roles: frozenset[str]

    def has_any(self, *roles: str) -> bool:
        return bool(self.roles.intersection(roles))


def _disabled_principal() -> Principal:
    return Principal(subject="local-dev", tenant_id="default", roles=frozenset({"admin", "knowledge_manager", "support", "viewer"}))


def get_principal(credentials: HTTPAuthorizationCredentials | None = Security(bearer)) -> Principal:
    if settings.auth_mode == "disabled":
        return _disabled_principal()
    if not credentials:
        raise HTTPException(status_code=401, detail="Bearer token required")
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=["HS256"],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            options={"require": ["exp", "iat", "sub", "tenant_id"]},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid bearer token") from exc
    roles = payload.get("roles") or []
    if not isinstance(roles, list):
        raise HTTPException(status_code=401, detail="Invalid roles claim")
    return Principal(subject=str(payload["sub"]), tenant_id=str(payload["tenant_id"]), roles=frozenset(map(str, roles)))


def require_roles(*roles: str) -> Callable:
    def dependency(principal: Principal = Depends(get_principal)) -> Principal:
        if not principal.has_any(*roles):
            raise HTTPException(status_code=403, detail="Insufficient role")
        return principal
    return dependency
