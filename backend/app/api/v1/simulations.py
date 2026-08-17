"""Endpoint 7. docs/API_CONTRACT.md section 8.7.

There is no GET route for a stored simulation: the frozen contract has exactly ten endpoints and
adding an eleventh is a Category C decision. Results are persisted (`simulations.result_json`) so
the capability exists the moment the contract makes room for it.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.schemas.simulation import SimulationRequest, SimulationResponse
from app.simulation import SimulationService

router = APIRouter(tags=["simulations"])


@router.post(
    "/simulations", response_model=SimulationResponse, response_model_exclude_unset=True
)
async def run_simulation(
    request: SimulationRequest, session: Session = Depends(get_session)
) -> SimulationResponse:
    return SimulationService(session).run(request)
