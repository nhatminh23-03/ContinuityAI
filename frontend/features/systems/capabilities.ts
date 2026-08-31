import type { CapabilityExposure, GraphEdge, GraphResponse, ReadinessLevel } from '@/types/api';
import { READINESS_SHORT_COPY } from '@/lib/copy';

/**
 * Pure projections of the graph payload for the System Detail panels.
 * Statuses and readiness labels are read from the payload, never derived —
 * counting and ordering received values is display work.
 */

export interface CapabilityRow {
  id: string;
  name: string;
  exposure: string | undefined;
  criticality: string | undefined;
}

export function capabilitiesFromGraph(graph: GraphResponse): CapabilityRow[] {
  return graph.nodes
    .filter((node) => node.type === 'CAPABILITY')
    .map((node) => ({
      id: node.id,
      name: node.label,
      exposure: node.status,
      criticality:
        typeof node.metadata?.operational_criticality === 'string'
          ? node.metadata.operational_criticality
          : undefined,
    }));
}

const READINESS_ORDER = ['VALIDATED', 'PRACTICED', 'ASSISTED', 'EXPOSED', 'NONE'] as const;

export function coverageSummary(edges: GraphEdge[], capabilityId: string): string {
  const counts = new Map<string, number>();
  for (const edge of edges) {
    if (edge.type !== 'DEMONSTRATES' || edge.target !== capabilityId) continue;
    const readiness = typeof edge.metadata?.readiness === 'string' ? edge.metadata.readiness : 'NONE';
    counts.set(readiness, (counts.get(readiness) ?? 0) + 1);
  }
  // Lowercasing the enum leaked "exposed" into the interface, where it reads as
  // the capability's risk state rather than what one engineer has done.
  const parts = READINESS_ORDER.filter((level) => counts.has(level)).map(
    (level) => `${counts.get(level)} ${READINESS_SHORT_COPY[level as ReadinessLevel]}`,
  );
  return parts.length > 0 ? parts.join(' · ') : 'No demonstrated coverage';
}

const SEVERITY: Record<string, number> = {
  CRITICAL_GAP: 3,
  DEGRADED: 2,
  INSUFFICIENT_EVIDENCE: 1,
  COVERED: 0,
};

/** Default panel selection: the first capability with the worst received status. */
export function defaultCapabilityId(capabilities: CapabilityRow[]): string | undefined {
  let best: CapabilityRow | undefined;
  let bestRank = -1;
  for (const capability of capabilities) {
    const rank = SEVERITY[capability.exposure as CapabilityExposure] ?? -1;
    if (rank > bestRank) {
      best = capability;
      bestRank = rank;
    }
  }
  return best?.id;
}
