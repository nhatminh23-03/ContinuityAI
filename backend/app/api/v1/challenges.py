"""Endpoint 11. PRD section 21, closing FR-020 and AC-11.

**This is an eleventh endpoint, and the frozen contract specified ten.** Adding one is a Category C
decision under `TEAM_WORKFLOW_PERSON_A_B.md` section 32, so it is logged as DEC-10 in
docs/DECISIONS.md and flagged in HANDOFF.md for Person B's acknowledgement.

The reasoning for building it rather than deferring again: `FR-020`, `AC-11`, user scenario S5, and
a domain entity all depend on it, and `OPEN-01` deferred the costing to a "Phase 7 checkpoint" that
arrives after the deadline — so the deferral was quietly turning into an omission. It is also much
cheaper now than when it was deferred, because `app/services/recompute.py` already exists and is
already exercised by the seed.

It is additive: nothing that previously worked changes, and the frontend can adopt it whenever the
provenance drawer is ready for a "Challenge Assessment" action.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.challenge import ChallengeService
from app.db.session import get_session
from app.schemas.challenge import ChallengeRequest, ChallengeResponse

router = APIRouter(tags=["challenges"])


@router.post(
    "/capabilities/{capability_id}/challenge",
    response_model=ChallengeResponse,
    response_model_exclude_unset=True,
    status_code=201,
)
async def challenge_assessment(
    capability_id: str, request: ChallengeRequest, session: Session = Depends(get_session)
) -> ChallengeResponse:
    # The manager supplies evidence or a correction. Readiness, exposure, and risk are recomputed
    # from it and reported back — there is no request field that could set them directly.
    return ChallengeService(session).submit(capability_id, request)
