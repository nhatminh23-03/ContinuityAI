'use client';

import { useMemo } from 'react';
import ReactFlow, { Controls, Handle, Position, type NodeProps, type NodeTypes } from 'reactflow';
import 'reactflow/dist/style.css';
import type { CapabilityExposure, GraphResponse } from '@/types/api';
import { toFlow } from './layout';

/**
 * The contextual graph. Solid DEMONSTRATES edges (thickness = received
 * readiness) against the one dashed DECLARED_OWNER edge is the product's
 * most important visual. Clicking a capability focuses its neighbourhood.
 */

const STATUS_DOT: Record<CapabilityExposure, string> = {
  COVERED: 'var(--status-covered)',
  DEGRADED: 'var(--status-degraded)',
  CRITICAL_GAP: 'var(--status-critical-gap)',
  INSUFFICIENT_EVIDENCE: 'var(--status-insufficient)',
};

function CenterHandles() {
  const hidden = {
    opacity: 0,
    pointerEvents: 'none' as const,
    left: '50%',
    top: '50%',
    transform: 'translate(-50%,-50%)',
    width: 1,
    height: 1,
    minWidth: 0,
    minHeight: 0,
    border: 'none',
  };
  return (
    <>
      <Handle type="target" position={Position.Top} style={hidden} />
      <Handle type="source" position={Position.Bottom} style={hidden} />
    </>
  );
}

function SystemNode({ data }: NodeProps) {
  return (
    <div className="rounded-2xl bg-slate-900 px-5 py-3 text-sm font-medium text-white shadow-lg">
      {data.label}
      <CenterHandles />
    </div>
  );
}

function ComponentNode({ data }: NodeProps) {
  return (
    <div className="rounded-full border border-slate-300/70 bg-white/70 px-3 py-1 text-[11px] font-medium text-slate-600 backdrop-blur">
      {data.label}
      <CenterHandles />
    </div>
  );
}

function CapabilityNode({ data }: NodeProps) {
  const status = data.status as CapabilityExposure | undefined;
  return (
    <div className="frosted-card cursor-pointer px-3.5 py-2 text-xs font-semibold text-slate-800">
      <span className="flex items-center gap-2">
        {status ? (
          <span
            aria-hidden
            className="h-2 w-2 rounded-full"
            style={{
              background: status === 'INSUFFICIENT_EVIDENCE' ? 'transparent' : STATUS_DOT[status],
              border:
                status === 'INSUFFICIENT_EVIDENCE'
                  ? `1.5px dashed ${STATUS_DOT[status]}`
                  : 'none',
            }}
          />
        ) : null}
        {data.label}
      </span>
      <CenterHandles />
    </div>
  );
}

function EngineerNode({ data }: NodeProps) {
  const initials = String(data.label)
    .split(/\s+/)
    .slice(0, 2)
    .map((word: string) => word[0]?.toUpperCase() ?? '')
    .join('');
  return (
    <div className="flex w-20 flex-col items-center gap-1">
      <span className="flex h-9 w-9 items-center justify-center rounded-full bg-white/80 text-xs font-semibold text-slate-700 shadow ring-1 ring-white/70">
        {initials}
      </span>
      <span className="text-center text-[10px] font-medium leading-tight text-slate-700">
        {data.label}
      </span>
      <CenterHandles />
    </div>
  );
}

function EvidenceNode({ data }: NodeProps) {
  return (
    <div className="rounded-lg border border-slate-300/60 bg-white/60 px-2 py-1 text-[9px] font-medium text-slate-500">
      {data.label}
      <CenterHandles />
    </div>
  );
}

const NODE_TYPES: NodeTypes = {
  system: SystemNode,
  component: ComponentNode,
  capability: CapabilityNode,
  engineer: EngineerNode,
  evidence: EvidenceNode,
};

export function SystemGraph({
  graph,
  focusId,
  onCapabilityClick,
  onEvidenceClick,
}: {
  graph: GraphResponse;
  focusId?: string;
  onCapabilityClick?: (capabilityId: string) => void;
  onEvidenceClick?: () => void;
}) {
  const { nodes, edges } = useMemo(() => toFlow(graph, focusId), [graph, focusId]);

  return (
    <div className="frosted-card h-[440px] overflow-hidden p-1">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={NODE_TYPES}
        fitView
        fitViewOptions={{ padding: 0.15 }}
        minZoom={0.3}
        nodesDraggable={false}
        nodesConnectable={false}
        edgesFocusable={false}
        proOptions={{ hideAttribution: false }}
        onNodeClick={(_, node) => {
          if (node.type === 'capability') onCapabilityClick?.(node.id);
          if (node.type === 'evidence') onEvidenceClick?.();
        }}
      >
        <Controls showInteractive={false} position="bottom-right" />
      </ReactFlow>
    </div>
  );
}
