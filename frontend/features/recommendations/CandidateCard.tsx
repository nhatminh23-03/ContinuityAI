import type { BackupCandidate } from '@/types/api';
import { EngineerBadge } from '@/components/people';

/**
 * One technical candidate: monochrome initials (never a photograph),
 * overlap as a neutral label (never a percentage), strengths, an honest
 * gap statement, and confidence with copy that says what it measures.
 */
export function CandidateCard({
  candidate,
  role,
  onGeneratePlan,
  onViewEvidence,
}: {
  candidate: BackupCandidate;
  role?: string;
  onGeneratePlan: () => void;
  onViewEvidence?: () => void;
}) {
  return (
    <div className="frosted-card flex flex-col p-6">
      <div className="flex items-start justify-between gap-3">
        <EngineerBadge name={candidate.name} role={role} />
        <div className="text-right">
          <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
            Technical overlap
          </div>
          <div className="text-lg font-medium text-slate-900">{candidate.technical_overlap}</div>
        </div>
      </div>

      {candidate.strengths.length > 0 ? (
        <div className="mt-5">
          <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
            Demonstrated strengths
          </div>
          <ul className="mt-2 flex flex-wrap gap-2">
            {candidate.strengths.map((strength) => (
              <li
                key={strength}
                className="rounded-full bg-white/60 px-3 py-1 text-xs font-medium text-slate-700 ring-1 ring-slate-900/5"
              >
                {strength}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {candidate.gaps.length > 0 ? (
        <div className="mt-4">
          <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
            Gaps to close
          </div>
          <ul className="mt-2 space-y-1.5">
            {candidate.gaps.map((gap) => (
              <li key={gap} className="flex items-start gap-2 text-xs text-slate-600">
                <span aria-hidden className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-slate-400" />
                {gap}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="mt-4 text-xs text-slate-600">
        Confidence in demonstrated coverage of this capability:{' '}
        <span className="font-semibold text-slate-700">{candidate.evidence_confidence}</span>
      </div>

      <div className="mt-auto flex items-center justify-between gap-3 pt-5">
        {onViewEvidence && candidate.supporting_evidence_ids.length > 0 ? (
          <button
            type="button"
            onClick={onViewEvidence}
            className="text-xs font-medium text-slate-600 underline decoration-slate-300 underline-offset-2 hover:text-slate-900"
          >
            View evidence ({candidate.supporting_evidence_ids.length})
          </button>
        ) : (
          <span />
        )}
        <button
          type="button"
          onClick={onGeneratePlan}
          className="motion-press rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
        >
          Generate transfer plan
        </button>
      </div>
    </div>
  );
}
