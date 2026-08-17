import type { PlatformSummary } from '@/types/api';
import { DriftLabel, RiskIndex } from '@/components/status';

/**
 * Platform overview card. No platform-level exposure pill (frozen out under
 * CI-10) and no single-expert count (no transport yet — GAP-01).
 */
export function PlatformCard({ platform }: { platform: PlatformSummary }) {
  return (
    <div className="frosted-card p-6">
      <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Platform</div>
      <div className="mt-1 text-2xl font-medium text-slate-900">{platform.name}</div>
      {platform.description ? (
        <p className="mt-1 text-sm text-slate-600">{platform.description}</p>
      ) : null}
      <div className="mt-6 flex items-end justify-between gap-4">
        <div>
          <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Highest system risk
          </div>
          <div className="mt-1">
            <RiskIndex value={platform.highest_system_risk_index} />
          </div>
        </div>
        <div className="flex flex-col items-end gap-1.5 pb-0.5 text-right">
          <span className="text-xs font-medium text-slate-600 tabular-nums">
            {platform.critical_gap_count} critical {platform.critical_gap_count === 1 ? 'gap' : 'gaps'}
          </span>
          <DriftLabel status={platform.drift_status} />
        </div>
      </div>
    </div>
  );
}
