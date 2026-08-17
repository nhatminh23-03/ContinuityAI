import type { SystemSummary } from '@/types/api';

/**
 * Display ordering of received values — descending by risk index, systems
 * without an index (INSUFFICIENT_EVIDENCE) last. Pure; does not mutate.
 */
export function sortSystemsByRisk(systems: SystemSummary[]): SystemSummary[] {
  return [...systems].sort((a, b) => {
    if (a.continuity_risk_index === null) return b.continuity_risk_index === null ? 0 : 1;
    if (b.continuity_risk_index === null) return -1;
    return b.continuity_risk_index - a.continuity_risk_index;
  });
}
