import type { CapabilityExposure, GraphEdge } from '@/types/api';
import { ExposurePill } from '@/components/status';
import { coverageSummary, type CapabilityRow } from './capabilities';

/**
 * The capability list: exposure pill plus a coverage summary of received
 * readiness labels. No ladder glyphs here (they belong to engineers) and no
 * activity metrics.
 */
export function CapabilityPanel({
  capabilities,
  edges,
  selectedId,
  onSelect,
}: {
  capabilities: CapabilityRow[];
  edges: GraphEdge[];
  selectedId: string | undefined;
  onSelect: (capabilityId: string) => void;
}) {
  return (
    <div className="frosted-card p-6">
      <h2 className="text-sm font-semibold text-slate-900">Capabilities</h2>
      <ul className="mt-3 divide-y divide-slate-900/5">
        {capabilities.map((capability) => {
          const selected = capability.id === selectedId;
          return (
            <li key={capability.id}>
              <button
                type="button"
                onClick={() => onSelect(capability.id)}
                aria-pressed={selected}
                className={`flex w-full items-center justify-between gap-3 rounded-xl px-2 py-3 text-left transition-colors ${
                  selected ? 'bg-white/60' : 'hover:bg-white/40'
                }`}
              >
                <span className="min-w-0">
                  <span className="block truncate text-sm font-medium text-slate-900">
                    {capability.name}
                  </span>
                  <span className="block text-xs text-slate-500">
                    {capability.criticality ? `Criticality ${capability.criticality} · ` : ''}
                    {coverageSummary(edges, capability.id)}
                  </span>
                </span>
                {capability.exposure ? (
                  <ExposurePill exposure={capability.exposure as CapabilityExposure} />
                ) : null}
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
