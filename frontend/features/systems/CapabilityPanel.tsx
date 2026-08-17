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
  onViewEvidence,
}: {
  capabilities: CapabilityRow[];
  edges: GraphEdge[];
  selectedId: string | undefined;
  onSelect: (capabilityId: string) => void;
  onViewEvidence?: (capabilityId: string) => void;
}) {
  return (
    <div className="frosted-card p-6">
      <h2 className="text-sm font-semibold text-slate-900">Capabilities</h2>
      <ul className="mt-3 divide-y divide-slate-900/5">
        {capabilities.map((capability) => {
          const selected = capability.id === selectedId;
          return (
            <li key={capability.id} className="py-1">
              <div
                className={`flex items-center gap-2 rounded-xl px-2 transition-colors ${
                  selected ? 'bg-white/60' : 'hover:bg-white/40'
                }`}
              >
                <button
                  type="button"
                  onClick={() => onSelect(capability.id)}
                  aria-pressed={selected}
                  className="flex min-w-0 flex-1 items-center justify-between gap-3 py-3 text-left"
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
                {onViewEvidence ? (
                  <button
                    type="button"
                    onClick={() => onViewEvidence(capability.id)}
                    className="shrink-0 rounded-lg px-2 py-1 text-[11px] font-medium text-slate-500 hover:bg-white/60 hover:text-slate-900"
                  >
                    Evidence
                  </button>
                ) : null}
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
