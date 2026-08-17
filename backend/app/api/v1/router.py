"""The API surface, all mounted under /api/v1.

Ten endpoints were frozen in docs/API_CONTRACT.md section 7. An eleventh —
`POST /capabilities/{id}/challenge` — was added to close FR-020 and AC-11, which had no other way
to be satisfied. That is a Category C decision, logged as DEC-10 in docs/DECISIONS.md.

Adding a twelfth is the same kind of decision, and the same bar applies.
"""

from fastapi import APIRouter, Depends

from . import (
    capabilities,
    challenges,
    mitigation_plans,
    platforms,
    recommendations,
    simulations,
    systems,
)

from app.core.security import require_token

# `require_token` is a no-op unless API_TOKEN is configured, so the default posture is unchanged.
api_router = APIRouter(prefix="/api/v1", dependencies=[Depends(require_token)])
api_router.include_router(platforms.router)
api_router.include_router(systems.router)
api_router.include_router(capabilities.router)
api_router.include_router(simulations.router)
api_router.include_router(recommendations.router)
api_router.include_router(mitigation_plans.router)
# Eleventh endpoint, added to close FR-020 and AC-11. Category C decision, logged as DEC-10.
api_router.include_router(challenges.router)
