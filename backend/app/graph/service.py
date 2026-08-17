"""Contextual knowledge graph. docs/ARCHITECTURE.md sections 24-25, API contract section 8.4.

Relational tables in, typed nodes and edges out. No graph database (decision frozen in
ARCHITECTURE.md section 93) — the graph semantics live in Python so traversal and simulation do
not depend on a storage product.

The graph is deliberately **contextual**, not the whole organisation. PRD section 11.3 and
ARCHITECTURE.md section 30 both warn about the enterprise hairball; a system-scoped neighbourhood
is readable and is what the demo needs.

One interpretation worth flagging. The contract's canonical direction for provenance is
`Coverage --SUPPORTED_BY--> Evidence`, but there is no `COVERAGE` node type in the frozen
`GraphNodeType` enum, so a coverage relationship has no id to be an edge endpoint. Evidence edges
are therefore emitted as `Engineer --SUPPORTED_BY--> Evidence` with the capability carried in edge
metadata, which preserves the full `(engineer, capability, evidence)` triple. Logged as DEC-08.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.repositories import (
    CapabilityRepository,
    CoverageRepository,
    EngineerRepository,
    EvidenceRepository,
    SystemRepository,
)
from app.schemas.enums import GraphEdgeType, GraphNodeType
from app.schemas.graph import GraphEdge, GraphNode, GraphResponse, GraphScope

# Evidence nodes are only included for a focused capability. Emitting every evidence node for a
# system would put hundreds of leaves on the canvas and bury the relationships that matter.
MAX_EVIDENCE_NODES = 12


class GraphService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def system_graph(self, system_id: str, focus_capability_id: str | None = None) -> GraphResponse:
        systems = SystemRepository(self.session)
        system = systems.get(system_id)
        if system is None:
            raise NotFoundError(f"System '{system_id}' not found.", {"system_id": system_id})

        components = systems.components(system_id)
        capabilities = CapabilityRepository(self.session).list_by_system(system_id)
        assessments = CapabilityRepository(self.session).assessments_for_system(system_id)
        system_assessment = systems.assessment(system_id)
        coverages = CoverageRepository(self.session).list_by_system(system_id)
        engineers = EngineerRepository(self.session).by_id()

        if focus_capability_id is not None:
            focus = CapabilityRepository(self.session).get(focus_capability_id)
            if focus is None or focus.system_id != system_id:
                raise NotFoundError(
                    f"Capability '{focus_capability_id}' is not part of system '{system_id}'.",
                    {"system_id": system_id, "capability_id": focus_capability_id},
                )
            capability_ids = {focus_capability_id}
            component_ids = {focus.component_id}
        else:
            capability_ids = {c.capability_id for c in capabilities}
            component_ids = {c.component_id for c in components}

        nodes: list[GraphNode] = [
            GraphNode(
                id=system.system_id,
                type=GraphNodeType.SYSTEM,
                label=system.name,
                status=system_assessment.exposure if system_assessment else None,
                metadata={"business_criticality": system.business_criticality},
            )
        ]
        edges: list[GraphEdge] = []

        for component in components:
            if component.component_id not in component_ids:
                continue
            nodes.append(
                GraphNode(
                    id=component.component_id,
                    type=GraphNodeType.COMPONENT,
                    label=component.name,
                    metadata={},
                )
            )
            edges.append(
                GraphEdge(
                    source=system.system_id,
                    target=component.component_id,
                    type=GraphEdgeType.HAS_COMPONENT,
                    metadata={},
                )
            )

        for capability in capabilities:
            if capability.capability_id not in capability_ids:
                continue
            assessment = assessments.get(capability.capability_id)
            nodes.append(
                GraphNode(
                    id=capability.capability_id,
                    type=GraphNodeType.CAPABILITY,
                    label=capability.name,
                    status=assessment.exposure if assessment else None,
                    metadata={"operational_criticality": capability.operational_criticality},
                )
            )
            edges.append(
                GraphEdge(
                    source=capability.component_id,
                    target=capability.capability_id,
                    type=GraphEdgeType.REQUIRES_CAPABILITY,
                    metadata={"operational_criticality": capability.operational_criticality},
                )
            )

        relevant = [c for c in coverages if c.capability_id in capability_ids]
        for coverage in sorted(relevant, key=lambda c: (c.capability_id, c.engineer_id)):
            engineer = engineers.get(coverage.engineer_id)
            if engineer is None:
                continue
            if not any(n.id == engineer.engineer_id for n in nodes):
                nodes.append(
                    GraphNode(
                        id=engineer.engineer_id,
                        type=GraphNodeType.ENGINEER,
                        label=engineer.name,
                        metadata={"role": engineer.role, "team": engineer.team},
                    )
                )
            edges.append(
                GraphEdge(
                    source=engineer.engineer_id,
                    target=coverage.capability_id,
                    type=GraphEdgeType.DEMONSTRATES,
                    metadata={
                        "readiness": coverage.readiness,
                        "freshness": coverage.freshness,
                        "evidence_confidence": coverage.evidence_confidence,
                    },
                )
            )

        # Declared ownership, kept visibly separate from demonstrated coverage. Without this edge
        # the declared-versus-demonstrated mismatch cannot be drawn at all (decision CI-05).
        declared = systems.declared_owner(system_id)
        if declared is not None:
            owner, source_reference = declared
            if not any(n.id == owner.engineer_id for n in nodes):
                nodes.append(
                    GraphNode(
                        id=owner.engineer_id,
                        type=GraphNodeType.ENGINEER,
                        label=owner.name,
                        metadata={"role": owner.role, "team": owner.team},
                    )
                )
            edges.append(
                GraphEdge(
                    source=owner.engineer_id,
                    target=system.system_id,
                    type=GraphEdgeType.DECLARED_OWNER,
                    metadata={"source": source_reference},
                )
            )

        if focus_capability_id is not None:
            self._add_evidence(nodes, edges, focus_capability_id)

        return GraphResponse(
            scope=GraphScope(type="SYSTEM", id=system.system_id, name=system.name),
            nodes=nodes,
            edges=edges,
        )

    def _add_evidence(
        self, nodes: list[GraphNode], edges: list[GraphEdge], capability_id: str
    ) -> None:
        records = EvidenceRepository(self.session).list_by_capability(capability_id)
        for record in records[:MAX_EVIDENCE_NODES]:
            nodes.append(
                GraphNode(
                    id=record.evidence_id,
                    type=GraphNodeType.EVIDENCE,
                    label=record.source_reference,
                    status=record.evidence_strength,
                    metadata={
                        "source_type": record.source_type,
                        "artifact_date": record.artifact_date.isoformat(),
                        "freshness": record.freshness,
                        "evidence_role": record.evidence_role,
                    },
                )
            )
            edges.append(
                GraphEdge(
                    source=record.engineer_id,
                    target=record.evidence_id,
                    type=GraphEdgeType.SUPPORTED_BY,
                    metadata={"capability_id": record.capability_id},
                )
            )
