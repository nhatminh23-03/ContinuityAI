"""Optional shared-token authentication.

`ARCHITECTURE.md` section 50 descopes enterprise IAM for the MVP, and that is the right call for a
hackathon. But the product serves per-person capability assessments, and "the manager approves a
plan" currently rests on a caller-supplied `approved_by` string — so shipping with no option at all
would leave a responsible-AI claim resting on nothing.

The compromise: a single shared bearer token, **off by default**.

* `API_TOKEN` unset — every endpoint is open, exactly as before. Local development and the frontend
  are unaffected, and nobody has to coordinate a secret to run the demo.
* `API_TOKEN` set — every `/api/v1` request must carry `Authorization: Bearer <token>`.

Deliberately not attempted: per-user identity, roles, sessions, or token rotation. A shared token
is honest about being a demo control rather than pretending to be authorisation.
"""

from __future__ import annotations

import secrets

from fastapi import Request

from app.core.config import settings
from app.core.errors import DomainError
from app.schemas.enums import ErrorCode


class UnauthorizedError(DomainError):
    """401. Kept in the same envelope as every other error so the frontend switches on `code`."""

    code = ErrorCode.UNAUTHORIZED


async def require_token(request: Request) -> None:
    """FastAPI dependency applied to the whole `/api/v1` router."""
    if not settings.api_token:
        return

    header = request.headers.get("authorization", "")
    scheme, _, presented = header.partition(" ")
    if scheme.lower() != "bearer" or not presented:
        raise UnauthorizedError(
            "This deployment requires a bearer token.",
            {"hint": "Send: Authorization: Bearer <API_TOKEN>"},
        )

    # Constant-time comparison. Cheap to do correctly, and a timing side channel on a shared
    # secret is the kind of detail that is embarrassing to explain later.
    if not secrets.compare_digest(presented, settings.api_token):
        raise UnauthorizedError("The bearer token presented is not valid.")
