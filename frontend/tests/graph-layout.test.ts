import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import type { GraphResponse } from '../types/api';
import { toFlow, DIMMED_OPACITY } from '../features/graph/layout';

const graph: GraphResponse = JSON.parse(
  readFileSync(resolve(__dirname, '../../fixtures/payment-gateway-graph.json'), 'utf8'),
);

describe('toFlow', () => {
  it('maps all 14 nodes to distinct deterministic positions', () => {
    const { nodes } = toFlow(graph);
    expect(nodes).toHaveLength(14);
    const positions = new Set(nodes.map((n) => `${n.position.x},${n.position.y}`));
    expect(positions.size).toBe(14);
    const again = toFlow(graph);
    expect(again.nodes.map((n) => n.position)).toEqual(nodes.map((n) => n.position));
  });

  it('renders exactly one dashed, labelled DECLARED_OWNER edge', () => {
    const { edges } = toFlow(graph);
    const declared = edges.filter((e) => e.data?.edgeType === 'DECLARED_OWNER');
    expect(declared).toHaveLength(1);
    expect(declared[0].source).toBe('eng_jordan_lee');
    expect(declared[0].target).toBe('system_payment_gateway');
    expect(declared[0].label).toBe('declared owner');
    expect(declared[0].style?.strokeDasharray).toBeTruthy();
  });

  it('scales DEMONSTRATES stroke width by received readiness', () => {
    const { edges } = toFlow(graph);
    const width = (source: string, target: string) =>
      edges.find((e) => e.source === source && e.target === target)?.style?.strokeWidth as number;
    const alex = width('eng_alex_chen', 'cap_incident_recovery'); // VALIDATED
    const maria = width('eng_maria_gomez', 'cap_incident_recovery'); // ASSISTED
    expect(alex).toBeGreaterThan(maria);
  });

  it('dims everything not connected to the focused capability', () => {
    const { nodes, edges } = toFlow(graph, 'cap_incident_recovery');
    const opacity = (id: string) => nodes.find((n) => n.id === id)?.style?.opacity;
    expect(opacity('cap_retry_logic')).toBe(DIMMED_OPACITY);
    expect(opacity('eng_lena_novak')).toBe(DIMMED_OPACITY);
    expect(opacity('component_transaction_processor')).toBe(DIMMED_OPACITY);
    expect(opacity('cap_incident_recovery')).toBeUndefined();
    expect(opacity('eng_alex_chen')).toBeUndefined();
    expect(opacity('system_payment_gateway')).toBeUndefined();
    const dimmedEdge = edges.find(
      (e) => e.source === 'eng_lena_novak' && e.target === 'cap_retry_logic',
    );
    expect(dimmedEdge?.style?.opacity).toBe(DIMMED_OPACITY);
  });
});
