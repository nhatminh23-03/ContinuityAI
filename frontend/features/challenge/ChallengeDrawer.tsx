'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import type {
  AssessmentSnapshot,
  ChallengeRequest,
  ChallengeType,
  EvidenceResponse,
  EvidenceRole,
  SystemSnapshot,
} from '@/types/api';
import { api } from '@/lib/api/endpoints';
import { ApiError } from '@/lib/api/client';
import { ExposurePill, RiskClassChip, RiskIndex } from '@/components/status';
import { ReadinessLadder } from '@/components/people';
import { ruleCopy } from '@/lib/copy';

/**
 * The challenge workflow (DEC-10). The governing rule is structural: this
 * form has no field for a readiness level, an exposure state, a confidence,
 * or a risk index. A manager changes evidence; the rules recompute.
 */

const CHALLENGE_TYPES: { value: ChallengeType; label: string; hint: string }[] = [
  {
    value: 'LINK_EVIDENCE',
    label: 'Link missed evidence',
    hint: 'Point at an existing artifact extraction missed. The engineer must be a recorded participant.',
  },
  {
    value: 'MANAGER_ATTESTATION',
    label: 'Manager attestation',
    hint: 'Record something no artifact captured. Attestations are capped at moderate strength.',
  },
  {
    value: 'CORRECT_CAPABILITY_MAPPING',
    label: 'Correct a mapping',
    hint: 'Move an evidence record to the capability it belongs to. Both capabilities recompute.',
  },
];

const ROLES: EvidenceRole[] = [
  'EXPOSURE',
  'CONTRIBUTION',
  'ASSISTED_EXECUTION',
  'INDEPENDENT_EXECUTION',
  'KNOWLEDGE_CAPTURE',
];

function SnapshotBlock({
  label,
  snapshot,
}: {
  label: string;
  snapshot: AssessmentSnapshot;
}) {
  return (
    <div className="rounded-xl bg-white/50 p-3">
      <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-2 flex flex-wrap items-center gap-2">
        <ExposurePill exposure={snapshot.exposure} />
        <RiskIndex value={snapshot.continuity_risk_index ?? null} size="md" />
        <RiskClassChip riskClass={snapshot.continuity_risk_class ?? null} />
      </div>
      {snapshot.readiness ? (
        <div className="mt-2">
          <ReadinessLadder level={snapshot.readiness} />
        </div>
      ) : null}
      {snapshot.rules_triggered?.length ? (
        <ul className="mt-2 space-y-0.5">
          {snapshot.rules_triggered.map((code) => (
            <li key={code} className="text-[11px] text-slate-600">
              · {ruleCopy(code)}
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

function SystemLine({ label, snapshot }: { label: string; snapshot: SystemSnapshot }) {
  return (
    <div className="flex flex-wrap items-center gap-2 text-xs text-slate-600 tabular-nums">
      <span className="font-semibold uppercase tracking-wide text-slate-500">{label}</span>
      <RiskIndex value={snapshot.continuity_risk_index ?? null} size="md" />
      <RiskClassChip riskClass={snapshot.continuity_risk_class ?? null} />
      <span>
        {snapshot.critical_gap_count} critical · {snapshot.degraded_capability_count} degraded ·{' '}
        {snapshot.covered_capability_count} covered
      </span>
    </div>
  );
}

export function ChallengeDrawer({
  capabilityId,
  capabilityName,
  evidenceResponse,
  onClose,
}: {
  capabilityId: string;
  capabilityName?: string;
  evidenceResponse?: EvidenceResponse;
  onClose: () => void;
}) {
  const panelRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();

  const [challengeType, setChallengeType] = useState<ChallengeType>('MANAGER_ATTESTATION');
  const [engineerId, setEngineerId] = useState('');
  const [sourceReference, setSourceReference] = useState('');
  const [evidenceRole, setEvidenceRole] = useState<EvidenceRole>('INDEPENDENT_EXECUTION');
  const [evidenceId, setEvidenceId] = useState('');
  const [targetCapabilityId, setTargetCapabilityId] = useState('');
  const [comment, setComment] = useState('');

  const engineers = useMemo(() => {
    const map = new Map<string, string>();
    for (const record of evidenceResponse?.evidence ?? []) {
      map.set(record.engineer_id, record.engineer_id);
    }
    for (const missing of evidenceResponse?.missing_evidence ?? []) {
      map.set(missing.engineer_id, missing.engineer_name);
    }
    return [...map.entries()].map(([id, name]) => ({ id, name }));
  }, [evidenceResponse]);

  useEffect(() => {
    const previouslyFocused = document.activeElement as HTMLElement | null;
    panelRef.current?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => {
      window.removeEventListener('keydown', onKey);
      previouslyFocused?.focus?.();
    };
  }, [onClose]);

  const mutation = useMutation({
    mutationFn: (body: ChallengeRequest) => api.challengeAssessment(capabilityId, body),
    onSuccess: () => {
      // Evidence changed and assessments recomputed; every reader refetches.
      queryClient.invalidateQueries();
    },
  });

  const submit = () => {
    const body: ChallengeRequest = {
      challenge_type: challengeType,
      submitted_by: 'eng_manager_sarah',
      comment,
      ...(challengeType !== 'CORRECT_CAPABILITY_MAPPING' && engineerId
        ? { engineer_id: engineerId }
        : {}),
      ...(challengeType === 'LINK_EVIDENCE' ? { source_reference: sourceReference } : {}),
      ...(challengeType === 'MANAGER_ATTESTATION' ? { evidence_role: evidenceRole } : {}),
      ...(challengeType === 'CORRECT_CAPABILITY_MAPPING'
        ? { evidence_id: evidenceId, target_capability_id: targetCapabilityId }
        : {}),
    };
    mutation.mutate(body);
  };

  const result = mutation.data;
  const canSubmit =
    comment.trim().length > 0 &&
    (challengeType === 'LINK_EVIDENCE'
      ? engineerId && sourceReference.trim()
      : challengeType === 'MANAGER_ATTESTATION'
        ? Boolean(engineerId)
        : evidenceId && targetCapabilityId.trim());

  const inputClass =
    'w-full rounded-lg border border-slate-900/10 bg-white/80 px-2.5 py-1.5 text-sm text-slate-800';
  const labelClass = 'block text-xs font-medium text-slate-600';

  return (
    <div className="fixed inset-0 z-[60]" role="dialog" aria-modal="true" aria-label="Challenge assessment">
      <button type="button" aria-label="Close" onClick={onClose} className="motion-fade absolute inset-0 bg-slate-900/40" />
      <div
        ref={panelRef}
        tabIndex={-1}
        className="glass-panel motion-drawer absolute inset-y-3 right-3 flex w-[520px] max-w-[calc(100vw-24px)] flex-col rounded-3xl outline-none"
      >
        <header className="flex items-center justify-between gap-3 border-b border-slate-900/5 px-6 py-4">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
              Challenge assessment
            </div>
            <div className="text-lg font-medium text-slate-900">
              {capabilityName ?? capabilityId}
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="flex h-8 w-8 items-center justify-center rounded-full text-slate-500 hover:bg-white/60 hover:text-slate-900"
          >
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-4 w-4" aria-hidden>
              <path d="m4 4 8 8m0-8-8 8" strokeLinecap="round" />
            </svg>
          </button>
        </header>

        <div className="min-h-0 flex-1 space-y-4 overflow-y-auto px-6 py-4">
          {!result ? (
            <>
              <p className="text-xs leading-relaxed text-slate-600">
                A manager changes evidence, never a score. The assessment recomputes from what you
                add or correct.
              </p>

              <div className="space-y-2">
                {CHALLENGE_TYPES.map((option) => (
                  <label
                    key={option.value}
                    className={`block cursor-pointer rounded-xl border px-3 py-2.5 ${
                      challengeType === option.value
                        ? 'border-slate-900/20 bg-white/70'
                        : 'border-slate-900/5 bg-white/40 hover:bg-white/60'
                    }`}
                  >
                    <span className="flex items-center gap-2">
                      <input
                        type="radio"
                        name="challenge-type"
                        checked={challengeType === option.value}
                        onChange={() => setChallengeType(option.value)}
                        className="accent-slate-900"
                      />
                      <span className="text-sm font-medium text-slate-900">{option.label}</span>
                    </span>
                    <span className="mt-1 block pl-6 text-xs text-slate-500">{option.hint}</span>
                  </label>
                ))}
              </div>

              {challengeType !== 'CORRECT_CAPABILITY_MAPPING' ? (
                <label className={labelClass}>
                  Engineer
                  <select
                    value={engineerId}
                    onChange={(event) => setEngineerId(event.target.value)}
                    className={`mt-1 ${inputClass}`}
                  >
                    <option value="">Select…</option>
                    {engineers.map((engineer) => (
                      <option key={engineer.id} value={engineer.id}>
                        {engineer.name}
                      </option>
                    ))}
                  </select>
                </label>
              ) : null}

              {challengeType === 'LINK_EVIDENCE' ? (
                <label className={labelClass}>
                  Artifact reference (for example INC-221)
                  <input
                    value={sourceReference}
                    onChange={(event) => setSourceReference(event.target.value)}
                    className={`mt-1 ${inputClass}`}
                    placeholder="INC-221"
                  />
                </label>
              ) : null}

              {challengeType === 'MANAGER_ATTESTATION' ? (
                <label className={labelClass}>
                  What the engineer did
                  <select
                    value={evidenceRole}
                    onChange={(event) => setEvidenceRole(event.target.value as EvidenceRole)}
                    className={`mt-1 ${inputClass}`}
                  >
                    {ROLES.map((role) => (
                      <option key={role} value={role}>
                        {role.replaceAll('_', ' ')}
                      </option>
                    ))}
                  </select>
                </label>
              ) : null}

              {challengeType === 'CORRECT_CAPABILITY_MAPPING' ? (
                <>
                  <label className={labelClass}>
                    Evidence record to move
                    <select
                      value={evidenceId}
                      onChange={(event) => setEvidenceId(event.target.value)}
                      className={`mt-1 ${inputClass}`}
                    >
                      <option value="">Select…</option>
                      {(evidenceResponse?.evidence ?? []).map((record) => (
                        <option key={record.evidence_id} value={record.evidence_id}>
                          {record.source_reference} — {record.evidence_id}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className={labelClass}>
                    Target capability id
                    <input
                      value={targetCapabilityId}
                      onChange={(event) => setTargetCapabilityId(event.target.value)}
                      className={`mt-1 ${inputClass}`}
                      placeholder="cap_retry_logic"
                    />
                  </label>
                </>
              ) : null}

              <label className={labelClass}>
                Why — part of the audit trail
                <textarea
                  value={comment}
                  onChange={(event) => setComment(event.target.value)}
                  rows={3}
                  className={`mt-1 ${inputClass}`}
                  placeholder="What the assessment missed and how you know."
                />
              </label>

              <p className="text-[11px] text-slate-500">
                Submitting as eng_manager_sarah. Previous and new assessments are both kept.
              </p>

              {mutation.isError ? (
                <p className="text-xs text-slate-600">
                  The challenge could not be submitted.
                  <span className="ml-1 text-slate-500">
                    {mutation.error instanceof ApiError
                      ? `Error code: ${mutation.error.code}`
                      : ''}
                  </span>
                </p>
              ) : null}
            </>
          ) : (
            <>
              <p className="text-sm text-slate-700">
                {result.recomputed
                  ? 'Evidence recorded and the assessment recomputed.'
                  : 'Evidence recorded. Nothing recomputed.'}
                {result.evidence_created ? (
                  <span className="mt-1 block text-xs text-slate-500">
                    Created: {result.evidence_created}
                  </span>
                ) : null}
                {result.evidence_moved ? (
                  <span className="mt-1 block text-xs text-slate-500">
                    Moved: {result.evidence_moved}
                  </span>
                ) : null}
              </p>
              <div className="grid grid-cols-2 gap-3">
                <SnapshotBlock label="Capability before" snapshot={result.capability_before} />
                <SnapshotBlock label="Capability after" snapshot={result.capability_after} />
              </div>
              <div className="space-y-1.5 rounded-xl bg-white/50 p-3">
                <SystemLine label="System before" snapshot={result.system_before} />
                <SystemLine label="System after" snapshot={result.system_after} />
              </div>
            </>
          )}
        </div>

        <footer className="flex items-center justify-end gap-3 border-t border-slate-900/5 px-6 py-4">
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl px-4 py-2 text-sm font-medium text-slate-600 hover:bg-white/50"
          >
            {result ? 'Done' : 'Cancel'}
          </button>
          {!result ? (
            <button
              type="button"
              disabled={!canSubmit || mutation.isPending}
              onClick={submit}
              className="motion-press rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
            >
              {mutation.isPending ? 'Submitting…' : 'Submit challenge'}
            </button>
          ) : null}
        </footer>
      </div>
    </div>
  );
}
