import type { EvidenceResponse } from '@/types/api';
import { ConfidenceLabel, ExposurePill } from '@/components/status';
import { ruleCopy } from '@/lib/copy';

/**
 * The assessment behind the evidence: exposure, confidence, fired rules,
 * and the declared-versus-demonstrated comparison.
 */
export function AssessmentCard({ response }: { response: EvidenceResponse }) {
  const { assessment, declared_vs_demonstrated: dvd } = response;
  return (
    <div className="frosted-card p-4">
      <div className="flex flex-wrap items-center gap-3">
        <h3 className="text-sm font-semibold text-slate-900">Assessment</h3>
        <ExposurePill exposure={assessment.exposure} />
        <ConfidenceLabel confidence={assessment.evidence_confidence} hint />
      </div>
      {assessment.rules_triggered?.length ? (
        <ul className="mt-3 space-y-1">
          {assessment.rules_triggered.map((code) => (
            <li key={code} className="flex items-start gap-2 text-xs text-slate-600">
              <span aria-hidden className="mt-1 h-1 w-1 shrink-0 rounded-full bg-slate-400" />
              {ruleCopy(code)}
            </li>
          ))}
        </ul>
      ) : null}
      {dvd ? (
        <div className="mt-4 rounded-xl bg-white/50 p-3">
          <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
            Declared vs demonstrated
          </div>
          <dl className="mt-2 space-y-1 text-xs text-slate-700">
            <div className="flex justify-between gap-3">
              <dt className="text-slate-500">Declared owner</dt>
              <dd className="font-medium">
                {dvd.declared_owner
                  ? `${dvd.declared_owner.name} (${dvd.declared_owner.source})`
                  : '—'}
              </dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="text-slate-500">Strongest demonstrated coverage</dt>
              <dd className="font-medium">{dvd.strongest_demonstrated_coverage?.name ?? '—'}</dd>
            </div>
          </dl>
          {dvd.mismatch_detected ? (
            <p className="mt-2 text-xs font-medium text-[color:var(--status-degraded)]">
              Differs from demonstrated coverage
            </p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
