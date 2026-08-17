import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import type { GraphResponse } from '../types/api';
import { capabilitiesFromGraph, coverageSummary, defaultCapabilityId } from '../features/systems/capabilities';

const graph: GraphResponse = JSON.parse(
  readFileSync(resolve(__dirname, '../../fixtures/payment-gateway-graph.json'), 'utf8'),
);

describe('capabilitiesFromGraph', () => {
  it('returns the five capabilities with their received statuses', () => {
    const capabilities = capabilitiesFromGraph(graph);
    expect(capabilities).toHaveLength(5);
    const byId = new Map(capabilities.map((c) => [c.id, c]));
    expect(byId.get('cap_incident_recovery')).toMatchObject({
      name: 'Incident Recovery',
      exposure: 'DEGRADED',
      criticality: 'CRITICAL',
    });
    expect(byId.get('cap_retry_logic')?.exposure).toBe('COVERED');
    const statuses = capabilities.map((c) => c.exposure);
    expect(statuses.filter((s) => s === 'DEGRADED')).toHaveLength(2);
    expect(statuses.filter((s) => s === 'COVERED')).toHaveLength(3);
  });
});

describe('coverageSummary', () => {
  it('counts DEMONSTRATES edges into the capability by readiness label', () => {
    expect(coverageSummary(graph.edges, 'cap_incident_recovery')).toBe(
      '1 validated · 1 assisted · 1 exposed',
    );
  });

  it('returns a quiet message when no coverage edges exist', () => {
    expect(coverageSummary(graph.edges, 'cap_nonexistent')).toBe('No demonstrated coverage');
  });
});

describe('defaultCapabilityId', () => {
  it('prefers the worst received status', () => {
    const capabilities = capabilitiesFromGraph(graph);
    expect(defaultCapabilityId(capabilities)).toBe('cap_incident_recovery');
  });
});
