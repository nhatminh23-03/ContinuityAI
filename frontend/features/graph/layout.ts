import type { Edge, Node } from 'reactflow';
import type { GraphEdge, GraphNode, GraphResponse } from '@/types/api';

/**
 * Pure projection of the graph payload into reactflow nodes and edges.
 *
 * Positions are fixed concentric bands — SYSTEM centre, COMPONENT ring,
 * CAPABILITY ring, ENGINEER outer ring, EVIDENCE leaves — computed
 * deterministically from index and count. No auto-layout dependency, so
 * there is nothing to fight (the brief's stated graph risk).
 *
 * Relationships come from the payload only; scaling a received readiness
 * label into a stroke width is display, not assessment.
 */

export const DIMMED_OPACITY = 0.18;

const RING_RADIUS: Record<GraphNode['type'], number> = {
  PLATFORM: 0,
  SYSTEM: 0,
  COMPONENT: 150,
  CAPABILITY: 300,
  ENGINEER: 460,
  EVIDENCE: 600,
};

const READINESS_WIDTH: Record<string, number> = {
  VALIDATED: 4,
  PRACTICED: 3,
  ASSISTED: 2,
  EXPOSED: 1.25,
  NONE: 1,
};

const CENTER = { x: 0, y: 0 };

function positionFor(type: GraphNode['type'], index: number, count: number) {
  if (type === 'SYSTEM' || type === 'PLATFORM') return { x: CENTER.x, y: CENTER.y - index * 80 };
  const radius = RING_RADIUS[type];
  // Stagger each ring's starting angle so rings do not align into a single spoke.
  const offset = {
    COMPONENT: -Math.PI / 2,
    CAPABILITY: -Math.PI / 2 + 0.35,
    ENGINEER: -Math.PI / 2 + 0.7,
    EVIDENCE: -Math.PI / 2 + 1.05,
  }[type];
  const angle = offset + (index / Math.max(count, 1)) * Math.PI * 2;
  return {
    x: Math.round(CENTER.x + radius * Math.cos(angle)),
    y: Math.round(CENTER.y + radius * Math.sin(angle)),
  };
}

/** Node ids that stay at full opacity when a capability is focused. */
function keptNodeIds(graph: GraphResponse, focusId: string): Set<string> {
  const kept = new Set<string>([focusId]);
  for (const edge of graph.edges) {
    if (edge.source === focusId) kept.add(edge.target);
    if (edge.target === focusId) kept.add(edge.source);
  }
  for (const node of graph.nodes) {
    // The system anchors the picture; evidence nodes only arrive server-filtered
    // to the focused capability, so both stay visible.
    if (node.type === 'SYSTEM' || node.type === 'EVIDENCE') kept.add(node.id);
  }
  return kept;
}

function edgeStyle(edge: GraphEdge): { style: Edge['style']; label?: string } {
  switch (edge.type) {
    case 'DEMONSTRATES': {
      const readiness =
        typeof edge.metadata?.readiness === 'string' ? edge.metadata.readiness : 'NONE';
      return {
        style: { stroke: '#64748b', strokeWidth: READINESS_WIDTH[readiness] ?? 1 },
      };
    }
    case 'DECLARED_OWNER':
      return {
        style: { stroke: '#64748b', strokeWidth: 1.5, strokeDasharray: '7 5' },
        label: 'declared owner',
      };
    case 'SUPPORTED_BY':
      return { style: { stroke: '#94a3b8', strokeWidth: 1, strokeDasharray: '2 4' } };
    default:
      return { style: { stroke: '#cbd5e1', strokeWidth: 1 } };
  }
}

export function toFlow(
  graph: GraphResponse,
  focusId?: string,
): { nodes: Node[]; edges: Edge[] } {
  const kept = focusId ? keptNodeIds(graph, focusId) : undefined;

  const countByType = new Map<string, number>();
  for (const node of graph.nodes) {
    countByType.set(node.type, (countByType.get(node.type) ?? 0) + 1);
  }
  const indexByType = new Map<string, number>();

  const nodes: Node[] = graph.nodes.map((node) => {
    const index = indexByType.get(node.type) ?? 0;
    indexByType.set(node.type, index + 1);
    const dimmed = kept !== undefined && !kept.has(node.id);
    return {
      id: node.id,
      type: node.type.toLowerCase(),
      position: positionFor(node.type, index, countByType.get(node.type) ?? 1),
      data: { label: node.label, status: node.status, metadata: node.metadata ?? {} },
      ...(dimmed ? { style: { opacity: DIMMED_OPACITY } } : {}),
    };
  });

  const edges: Edge[] = graph.edges.map((edge, index) => {
    const { style, label } = edgeStyle(edge);
    const dimmed =
      kept !== undefined && !(kept.has(edge.source) && kept.has(edge.target));
    return {
      id: `${edge.type}:${edge.source}->${edge.target}:${index}`,
      source: edge.source,
      target: edge.target,
      type: 'straight',
      label,
      labelStyle: { fontSize: 10, fill: '#475569', fontWeight: 600 },
      labelBgStyle: { fill: 'rgba(255,255,255,0.8)' },
      data: { edgeType: edge.type, metadata: edge.metadata ?? {} },
      style: { ...style, ...(dimmed ? { opacity: DIMMED_OPACITY } : {}) },
    };
  });

  return { nodes, edges };
}
