"""The 10 frozen endpoints, all mounted under /api/v1.

Adding an 11th is a Category C decision. docs/API_CONTRACT.md section 7.
"""

from fastapi import APIRouter

from . import capabilities, mitigation_plans, platforms, recommendations, simulations, systems

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(platforms.router)
api_router.include_router(systems.router)
api_router.include_router(capabilities.router)
api_router.include_router(simulations.router)
api_router.include_router(recommendations.router)
api_router.include_router(mitigation_plans.router)
