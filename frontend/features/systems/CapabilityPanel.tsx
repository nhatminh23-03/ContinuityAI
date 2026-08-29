import type {
  CapabilityExposure,
  ComponentSummary,
  GraphEdge,
  OperationalCriticality,
} from '@/types/api';
import { CRITICALITY_COPY } from '@/lib/copy';
import { ExposurePill } from '@/components/status';
import { coverageSummary, type CapabilityRow } from './capabilities';

/**
 * The capability list: exposure pill plus a coverage summary of received
 * readiness labels. No ladder glyphs here (they belong to engineers) and no
 * activity metrics.
 */
export function CapabilityPanel({
  capabilities,
  components,
  edges,
  selectedId,
  onSelect,
  onViewEvidence,
}: {
  capabilities: CapabilityRow[];
  /** Received containment. Grouping is presentation; it never changes selection. */
  components: ComponentSummary[];
  edges: GraphEdge[];
  selectedId: string | undefined;
  onSelect: (capabilityId: string) => void;
  onViewEvidence?: (capabilityId: string) => void;
}) {
  // Presentation only. `defaultCapabilityId` still selects from the ungrouped
  // list, so which capability the golden path starts on is byte-identical.
  const claimed = new Set<string>();
  const groups: { key: string; name: string; rows: CapabilityRow[] }[] = [];
  for (const component of components) {
    const rows = capabilities.filter((c) => component.capability_ids.includes(c.id));
    rows.forEach((row) => claimed.add(row.id));
    if (rows.length > 0) {
      groups.push({ key: component.component_id, name: component.name, rows });
    }
  }
  // Nothing should land here on current data; it exists so a capability cannot
  // silently vanish if the graph and the detail payload ever disagree.
  const orphans = capabilities.filter((c) => !claimed.has(c.id));
  if (orphans.length > 0) {
    groups.push({ key: '__unclaimed', name: 'Not linked to a component', rows: orphans });
  }

  return (
    <div className="frosted-card p-6">
      <h2 className="text-sm font-semibold text-slate-900">Capabilities</h2>
      <p className="mt-0.5 text-xs text-slate-500">
        Grouped by the component that requires them.
      </p>
      {groups.map((group) => (
        <div key={group.key}>
          <h3 className="px-2 pt-3 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
            {group.name}
          </h3>
          <ul className="motion-stagger divide-y divide-slate-900/5">
            {group.rows.map((capability) => {
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
                        {capability.criticality
                              ? `${CRITICALITY_COPY[capability.criticality as OperationalCriticality]} importance · `
                              : ''}
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
      ))}
    </div>
  );
}
