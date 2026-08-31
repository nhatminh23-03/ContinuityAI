"""Ask the model to assess every system's business criticality, and compare it to the humans. FR-010.

    python -m scripts.suggest_criticality                  # from backend/
    python -m scripts.suggest_criticality --provider openrouter

Nothing is written to the database and no demo number moves. Every seeded system is
`HUMAN_CONFIRMED`, and under `app/ai/criticality.py` a human-confirmed value is authoritative, so this
is a *comparison* rather than an override — which is the interesting output anyway. Agreement across
five independently human-assigned values is a checkable statement about whether the model understands
the estate; a disagreement is a question for a manager, not a defect.

The model is given each system's purpose, components and capabilities. It is deliberately given no
engineer, no headcount and no activity volume, because those inputs would turn "how important is this
system" into "how busy is this team" — the inference this product exists to argue against.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.ai.criticality import SystemDescription, agreement, suggest  # noqa: E402
from app.ai.provider import get_provider  # noqa: E402
from app.db.session import session_scope  # noqa: E402
from app.models import Capability, Component, Platform, System  # noqa: E402
from app.schemas.enums import BusinessCriticality  # noqa: E402


def describe(session, system: System) -> SystemDescription:
    platform = session.get(Platform, system.platform_id)
    components = (
        session.query(Component).filter(Component.system_id == system.system_id).all()
    )
    capabilities = (
        session.query(Capability).filter(Capability.system_id == system.system_id).all()
    )
    return SystemDescription(
        system_id=system.system_id,
        name=system.name,
        description=system.description or "",
        platform_name=platform.name if platform else "(unknown platform)",
        component_names=[c.name for c in components],
        capability_names=[c.name for c in capabilities],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", default=None, help="override AI_PROVIDER for this run")
    args = parser.parse_args()

    provider = get_provider(args.provider)
    chat = getattr(provider, "_chat", None)
    if chat is None:
        print(
            f"provider '{provider.name}' has no model transport, so it cannot suggest criticality. "
            f"FR-010 says AI *may* suggest — with no model there is nothing to ask. Use "
            f"--provider chain or --provider openrouter."
        )
        return 1

    label = f"{provider.name}/{getattr(provider, 'model_id', 'n/a')}"
    print(f"criticality suggestions from {label}\n" + "=" * 72)

    agreed = 0
    total = 0
    with session_scope() as session:
        systems = session.query(System).order_by(System.position).all()
        for system in systems:
            total += 1
            human = BusinessCriticality(system.business_criticality)
            suggestion = suggest(describe(session, system), chat=chat, provider_label=label)
            verdict = agreement(human, suggestion)
            if verdict == "agrees":
                agreed += 1

            print(f"\n{system.name}  ({system.system_id})")
            print(f"  human      {human.value}  [{system.criticality_source}]")
            if suggestion is None:
                print("  model      no usable suggestion")
                continue
            print(
                f"  model      {suggestion.business_criticality.value}  "
                f"(confidence {suggestion.confidence.value})"
            )
            print(f"  because    {suggestion.rationale}")
            print(f"  verdict    {verdict}")

    print("\n" + "=" * 72)
    print(f"model agrees with {agreed} of {total} human-confirmed values")
    print(
        "Human-confirmed values are authoritative and were not changed (FR-010). A disagreement is "
        "a question for a manager, not an error."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
