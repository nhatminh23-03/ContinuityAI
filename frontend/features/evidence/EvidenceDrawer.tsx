'use client';

import { useEffect, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api, queryKeys } from '@/lib/api/endpoints';
import { ApiError } from '@/lib/api/client';
import { AssessmentCard } from './AssessmentCard';
import { EvidenceCard } from './EvidenceCard';
import { ChallengeDrawer } from '@/features/challenge/ChallengeDrawer';

/**
 * The provenance drawer — every readiness claim opens into its evidence.
 * Absence of evidence renders as absence of evidence, never as inability.
 */
export function EvidenceDrawer({
  capabilityId,
  engineerId,
  engineerName,
  onClose,
}: {
  capabilityId: string;
  engineerId?: string;
  engineerName?: string;
  onClose: () => void;
}) {
  const drawerRef = useRef<HTMLDivElement>(null);
  const [challengeOpen, setChallengeOpen] = useState(false);

  const query = useQuery({
    queryKey: queryKeys.capabilityEvidence(capabilityId, engineerId),
    queryFn: () => api.getCapabilityEvidence(capabilityId, engineerId),
  });

  useEffect(() => {
    const previouslyFocused = document.activeElement as HTMLElement | null;
    drawerRef.current?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => {
      window.removeEventListener('keydown', onKey);
      previouslyFocused?.focus?.();
    };
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50" role="dialog" aria-modal="true" aria-label="Evidence">
      <button
        type="button"
        aria-label="Close evidence drawer"
        onClick={onClose}
        className="motion-fade absolute inset-0 bg-slate-900/40"
      />
      <div
        ref={drawerRef}
        tabIndex={-1}
        className="glass-panel motion-drawer absolute inset-y-3 right-3 flex w-[520px] max-w-[calc(100vw-24px)] flex-col rounded-3xl outline-none"
      >
        <header className="flex items-center gap-3 border-b border-slate-900/5 px-6 py-4">
          <div className="min-w-0">
            <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
              Evidence · {query.data?.capability.name ?? capabilityId}
            </div>
            <div className="truncate text-lg font-medium text-slate-900">
              {engineerName ?? engineerId ?? 'All engineers'}
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="ml-auto flex h-8 w-8 items-center justify-center rounded-full text-slate-500 hover:bg-white/60 hover:text-slate-900"
          >
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-4 w-4" aria-hidden>
              <path d="m4 4 8 8m0-8-8 8" strokeLinecap="round" />
            </svg>
          </button>
        </header>

        <div className="min-h-0 flex-1 space-y-4 overflow-y-auto px-6 py-4">
          {query.isPending ? (
            <>
              <div className="frosted-card h-32 skeleton" />
              <div className="frosted-card h-40 skeleton" />
            </>
          ) : query.isError ? (
            <div className="frosted-card p-4 text-sm text-slate-600">
              Evidence could not be loaded.
              <span className="mt-1 block text-xs text-slate-500">
                {query.error instanceof ApiError ? `Error code: ${query.error.code}` : ''}
              </span>
            </div>
          ) : (
            <>
              <AssessmentCard response={query.data} />

              <h3 className="pt-1 text-sm font-semibold text-slate-900">Supporting evidence</h3>
              {query.data.evidence.length === 0 ? (
                <p className="text-sm text-slate-500">
                  No qualifying evidence records for this view.
                </p>
              ) : (
                query.data.evidence.map((record) => (
                  <EvidenceCard key={record.evidence_id} record={record} />
                ))
              )}

              {query.data.missing_evidence.length > 0 ? (
                <>
                  <h3 className="pt-1 text-sm font-semibold text-slate-900">Missing evidence</h3>
                  <ul className="motion-stagger space-y-2">
                    {query.data.missing_evidence.map((missing) => (
                      <li
                        key={missing.engineer_id}
                        className="pill-insufficient rounded-xl px-3 py-2 text-xs text-slate-600"
                      >
                        <span className="font-medium text-slate-700">{missing.engineer_name}</span>{' '}
                        — {missing.description}
                      </li>
                    ))}
                  </ul>
                </>
              ) : null}

              {query.data.conflicting_evidence?.length ? (
                <>
                  <h3 className="pt-1 text-sm font-semibold text-slate-900">
                    Conflicting evidence — sources disagree
                  </h3>
                  {query.data.conflicting_evidence.map((record) => (
                    <EvidenceCard key={record.evidence_id} record={record} />
                  ))}
                </>
              ) : null}
            </>
          )}
        </div>

        <footer className="flex items-center justify-end gap-3 border-t border-slate-900/5 px-6 py-4">
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl px-4 py-2 text-sm font-medium text-slate-600 hover:bg-white/50"
          >
            Close
          </button>
          <button
            type="button"
            disabled={!query.data}
            onClick={() => setChallengeOpen(true)}
            className="motion-press rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
          >
            Challenge assessment
          </button>
        </footer>
      </div>

      {challengeOpen ? (
        <ChallengeDrawer
          capabilityId={capabilityId}
          capabilityName={query.data?.capability.name}
          evidenceResponse={query.data}
          onClose={() => setChallengeOpen(false)}
        />
      ) : null}
    </div>
  );
}
