"""Endpoint 7. docs/API_CONTRACT.md section 8.7."""

from fastapi import APIRouter

from app.core.fixtures import load
from app.schemas.simulation import SimulationRequest, SimulationResponse

router = APIRouter(tags=["simulations"])


@router.post("/simulations", response_model=SimulationResponse, response_model_exclude_unset=True)
async def run_simulation(request: SimulationRequest) -> dict:
    return load("alex-simulation")
