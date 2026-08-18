import type { CapabilityImpact } from '@/types/api';
import { ExposurePill } from '@/components/status';
import { ReadinessLadder } from '@/components/people';

/**
 * One capability's before → after transition, with the best remaining
 * readiness — showing what survives is what keeps the analysis credible.
 */
export function ImpactRow({ impact }: { impact: CapabilityImpact }) {
  const changed = impact.before !== impact.after;
  return (
    <li className="flex flex-wrap items-center gap-x-4 gap-y-2 py-3">
      <div className="min-w-0 flex-1">
        <div className="truncate text-sm font-medium text-slate-900">{impact.name}</div>
        <div className="text-xs text-slate-500">Criticality {impact.operational_criticality}</div>
      </div>
      <div className="flex items-center gap-2">
        <ExposurePill exposure={impact.before} />
        <span aria-hidden className="text-slate-400">
          →
        </span>
        <ExposurePill exposure={impact.after} />
        {!changed ? <span className="text-[11px] font-medium text-slate-500">unchanged</span> : null}
      </div>
      <div className="flex w-56 items-center justify-end gap-2">
        <span className="text-[11px] text-slate-500">best remaining</span>
        <ReadinessLadder level={impact.remaining_best_readiness} />
      </div>
    </li>
  );
}
