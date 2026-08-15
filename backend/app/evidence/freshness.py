"""Evidence freshness. PRD section 16.3, reduced to three values by contract decision CI-04.

    FRESH   up to 18 months old
    AGING   18 to 36 months
    STALE   over 36 months

The PRD's rule also folds in "component change since the artifact date": evidence about code
that has since been rewritten is worth less regardless of its age. **That half is not
implemented.** Nothing in the schema expresses component change — there is no field, no table,
and no metric for it, and inventing one from commit counts would produce a number nobody could
defend. Age alone is implemented, and the gap is recorded in RECOMMENDATIONS.md R-05.

Freshness is computed against `settings.reference_date` rather than the wall clock so a seeded
demo cannot quietly reclassify itself between now and judging.
"""

from __future__ import annotations

from datetime import date

from app.core.config import settings
from app.schemas.enums import Freshness

FRESH_MAX_DAYS = 548  # ~18 months
AGING_MAX_DAYS = 1096  # ~36 months

FRESHNESS_RANK: dict[Freshness, int] = {
    Freshness.STALE: 0,
    Freshness.AGING: 1,
    Freshness.FRESH: 2,
}


def freshness_for(artifact_date: date, reference_date: date | None = None) -> Freshness:
    reference = reference_date or settings.reference_date
    age_days = (reference - artifact_date).days
    if age_days <= FRESH_MAX_DAYS:
        return Freshness.FRESH
    if age_days <= AGING_MAX_DAYS:
        return Freshness.AGING
    return Freshness.STALE


def best_freshness(values: list[Freshness | str]) -> Freshness:
    """Freshness of a coverage relationship is that of its most recent qualifying evidence."""
    if not values:
        return Freshness.STALE
    return max(
        (Freshness(v) if isinstance(v, str) else v for v in values),
        key=lambda f: FRESHNESS_RANK[f],
    )
