import type { SystemDetail } from '@/types/api';
import { RiskClassChip, RiskIndex } from '@/components/status';

/**
 * The four headline cells. "Capabilities without resilient backup" is the
 * demo script's own wording for degraded_capability_count; the true
 * single-expert count has no transport yet (GAP-01).
 */
export function MetricStrip({
  system,
  onWhyClick,
}: {
  system: SystemDetail;
  onWhyClick?: () => void;
}) {
  return (
    <div className="frosted-card grid grid-cols-2 gap-y-6 p-6 lg:grid-cols-4 lg:gap-y-0">
      <div className="lg:border-r lg:border-slate-900/5 lg:pr-6">
        <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Continuity Risk Index
        </div>
        <div className="mt-2 flex items-center gap-3">
          <RiskIndex value={system.continuity_risk_index} />
          <RiskClassChip riskClass={system.continuity_risk_class} />
        </div>
        <button
          type="button"
          onClick={onWhyClick}
          disabled={!onWhyClick}
          className="mt-2 text-xs font-medium text-slate-600 underline decoration-slate-300 underline-offset-2 hover:text-slate-900 disabled:cursor-default disabled:opacity-50"
          title={onWhyClick ? undefined : 'Arrives with the Why panel'}
        >
          Why this risk?
        </button>
      </div>
      <div className="lg:border-r lg:border-slate-900/5 lg:px-6">
        <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Capabilities without resilient backup
        </div>
        <div className="mt-2">
          <RiskIndex value={system.degraded_capability_count} />
        </div>
      </div>
      <div className="lg:border-r lg:border-slate-900/5 lg:px-6">
        <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Critical gaps
        </div>
        <div className="mt-2">
          <RiskIndex value={system.critical_gap_count} />
        </div>
      </div>
      <div className="lg:pl-6">
        <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Evidence confidence
        </div>
        <div className="mt-3 text-2xl font-light text-slate-900">{system.evidence_confidence}</div>
      </div>
    </div>
  );
}
