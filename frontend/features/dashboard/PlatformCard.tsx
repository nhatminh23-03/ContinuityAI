import type { PlatformSummary } from '@/types/api';
import { DriftLabel, MetricLabel, RiskIndex } from '@/components/status';
import { HINT_COPY } from '@/lib/copy';
import { InfoHint } from '@/components/InfoHint';

/**
 * Platform overview card. No platform-level exposure pill (frozen out under CI-10).
 *
 * `single_expert_dependency_count` now has transport (DEC-17 closed GAP-01) and is rendered
 * straight from the response. It is deliberately not derived from the degraded counts: under
 * DEC-07 those also include capabilities with no adequate engineer at all, so the two numbers
 * answer different questions. Copy stays descriptive — it reports what the evidence shows, not
 * a judgement about anyone.
 */
export function PlatformCard({ platform }: { platform: PlatformSummary }) {
  return (
    <div className="frosted-card p-6">
      <div className="inline-flex items-center gap-1 text-xs font-semibold uppercase tracking-wide text-slate-500">
        Platform
        <InfoHint label="platform" text={HINT_COPY.platform} />
      </div>
      <div className="mt-1 text-2xl font-medium text-slate-900">{platform.name}</div>
      {platform.description ? (
        <p className="mt-1 text-sm text-slate-600">{platform.description}</p>
      ) : null}
      {/* Containment, stated. Nothing else on the dashboard said that the rows in
          the table below are these cards' contents. */}
      <div className="mt-1 text-xs text-slate-500">
        {platform.system_count} {platform.system_count === 1 ? 'system' : 'systems'}
      </div>
      <div className="mt-6 flex items-end justify-between gap-4">
        <div>
          <MetricLabel hint={HINT_COPY.highestSystemRisk}>Highest system risk</MetricLabel>
          <div className="mt-1">
            <RiskIndex value={platform.highest_system_risk_index} />
          </div>
        </div>
        <div className="flex flex-col items-end gap-1.5 pb-0.5 text-right">
          <span className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
            Across this platform
          </span>
          <span className="text-xs font-medium text-slate-600 tabular-nums">
            {platform.critical_gap_count}{' '}
            {platform.critical_gap_count === 1 ? 'capability' : 'capabilities'} with no proven coverage
          </span>
          <span className="text-xs font-medium text-slate-600 tabular-nums">
            {platform.single_expert_dependency_count}{' '}
            {platform.single_expert_dependency_count === 1 ? 'capability depends' : 'capabilities depend'}{' '}
            on one person
          </span>
          <DriftLabel status={platform.drift_status} />
        </div>
      </div>
    </div>
  );
}
