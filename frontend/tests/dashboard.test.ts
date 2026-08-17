import { describe, expect, it } from 'vitest';
import type { SystemSummary } from '../types/api';
import { sortSystemsByRisk } from '../features/dashboard/sort';

const system = (id: string, index: number | null): SystemSummary => ({
  system_id: id,
  platform_id: 'platform_payments',
  name: id,
  description: null,
  business_criticality: 'HIGH',
  continuity_risk_index: index,
  continuity_risk_class: index === null ? null : 'HIGH',
  exposure: 'DEGRADED',
  evidence_confidence: 'MEDIUM',
  critical_gap_count: 0,
  degraded_capability_count: 0,
  covered_capability_count: 0,
  insufficient_evidence_count: 0,
  drift_status: 'STABLE',
});

describe('sortSystemsByRisk', () => {
  it('sorts descending by risk index with nulls last, without mutating input', () => {
    const input = [system('b', 52), system('a', 74), system('c', null), system('d', 68)];
    const sorted = sortSystemsByRisk(input);
    expect(sorted.map((s) => s.system_id)).toEqual(['a', 'd', 'b', 'c']);
    expect(input.map((s) => s.system_id)).toEqual(['b', 'a', 'c', 'd']);
  });
});
