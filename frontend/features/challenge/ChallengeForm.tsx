'use client';

import { useMemo, useState } from 'react';
import { useMutation, useQueries, useQuery, useQueryClient } from '@tanstack/react-query';
import type {
  AssessmentSnapshot,
  ChallengeRequest,
  ChallengeType,
  EvidenceResponse,
  EvidenceRole,
  SystemSnapshot,
} from '@/types/api';
import { api, queryKeys } from '@/lib/api/endpoints';
import { ApiError } from '@/lib/api/client';
import { ExposurePill, RiskClassChip, RiskIndex } from '@/components/status';
import { ReadinessLadder } from '@/components/people';
import { approverCopy, CHALLENGE_COPY, EVIDENCE_ROLE_COPY, ruleCopy } from '@/lib/copy';
import { capabilitiesFromGraph } from '@/features/systems/capabilities';

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
    hint: 'Pull a record that belongs here but was filed under another capability of the same system. Both capabilities recompute.',
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

export function ChallengeForm({
  capabilityId,
  evidenceResponse,
  seedEngineerId,
  seedEngineerName,
  onBack,
}: {
  capabilityId: string;
  evidenceResponse?: EvidenceResponse;
  /** The engineer the drawer is scoped to, or the missing-evidence row clicked. */
  seedEngineerId?: string;
  seedEngineerName?: string;
  onBack: () => void;
}) {
  const queryClient = useQueryClient();

  const [challengeType, setChallengeType] = useState<ChallengeType>('MANAGER_ATTESTATION');
  const [engineerId, setEngineerId] = useState(seedEngineerId ?? '');
  const [sourceReference, setSourceReference] = useState('');
  const [evidenceRole, setEvidenceRole] = useState<EvidenceRole>('INDEPENDENT_EXECUTION');
  const [evidenceId, setEvidenceId] = useState('');
  const [comment, setComment] = useState('');

  // EvidenceResponse carries no engineer roster — its records hold an id and no
  // name, and only missing_evidence carries one — so the id was being used as
  // its own label and the engineers who actually have evidence, the ones most
  // likely to be challenged, appeared as database keys. The capability's
  // engineer_coverage does carry names, and CoverageCard has usually already
  // fetched it under this exact key, so this is a cache read rather than a
  // round trip. An engineer named nowhere still keeps the id rather than
  // disappearing from the list.
  const capabilityQuery = useQuery({
    queryKey: queryKeys.capability(capabilityId),
    queryFn: () => api.getCapability(capabilityId),
  });

  const engineers = useMemo(() => {
    const names = new Map<string, string>();
    for (const coverage of capabilityQuery.data?.engineer_coverage ?? []) {
      names.set(coverage.engineer_id, coverage.name);
    }
    for (const missing of evidenceResponse?.missing_evidence ?? []) {
      names.set(missing.engineer_id, missing.engineer_name);
    }
    if (seedEngineerId && seedEngineerName) names.set(seedEngineerId, seedEngineerName);

    const map = new Map<string, string>();
    for (const record of evidenceResponse?.evidence ?? []) {
      map.set(record.engineer_id, names.get(record.engineer_id) ?? record.engineer_id);
    }
    for (const [id, name] of names) map.set(id, name);
    return [...map.entries()].map(([id, name]) => ({ id, name }));
  }, [capabilityQuery.data, evidenceResponse, seedEngineerId, seedEngineerName]);


  /**
   * The server moves the chosen record INTO the capability this drawer is open
   * on (`challenge/service.py::_correct_mapping`), and rejects any record
   * already filed here. The dropdown was populated from this capability's own
   * evidence, so every option it offered was one the server would refuse. The
   * records that can actually move are the ones filed under the *other*
   * capabilities of the same system — a cross-system move is refused outright —
   * so those are fetched, and only once this mode is selected.
   */
  const mappingMode = challengeType === 'CORRECT_CAPABILITY_MAPPING';
  const systemId = capabilityQuery.data?.system_id;

  const graphQuery = useQuery({
    queryKey: queryKeys.systemGraph(systemId ?? ''),
    queryFn: () => api.getSystemGraph(systemId!),
    enabled: mappingMode && Boolean(systemId),
  });

  const siblings = (
    graphQuery.data ? capabilitiesFromGraph(graphQuery.data) : []
  ).filter((row) => row.id !== capabilityId);

  const siblingEvidence = useQueries({
    queries: siblings.map((row) => ({
      queryKey: queryKeys.capabilityEvidence(row.id),
      queryFn: () => api.getCapabilityEvidence(row.id),
      enabled: mappingMode,
    })),
  });

  const movable = siblings.flatMap((row, index) =>
    (siblingEvidence[index]?.data?.evidence ?? []).map((record) => ({
      record,
      capabilityName: row.name,
    })),
  );
  const movableLoading =
    mappingMode &&
    (capabilityQuery.isPending ||
      graphQuery.isPending ||
      siblingEvidence.some((result) => result.isPending));

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
      comment: comment.trim(),
      ...(challengeType !== 'CORRECT_CAPABILITY_MAPPING' && engineerId
        ? { engineer_id: engineerId }
        : {}),
      ...(challengeType === 'LINK_EVIDENCE'
        ? { source_reference: sourceReference.trim() }
        : {}),
      ...(challengeType === 'MANAGER_ATTESTATION' ? { evidence_role: evidenceRole } : {}),
      ...(challengeType === 'CORRECT_CAPABILITY_MAPPING'
        ? {
            evidence_id: evidenceId,
            // The service ignores this field entirely — it appears once in the
            // backend, in the request schema, and nothing reads it — and moves
            // the record into the capability from the URL. Sending that id
            // keeps the request a truthful description of what happens, and
            // makes it correct if the field is ever wired up. Raised for
            // Person A rather than changed here.
            target_capability_id: capabilityId,
          }
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
        : Boolean(evidenceId));

  const inputClass =
    'w-full rounded-lg border border-slate-900/10 bg-white/80 px-2.5 py-1.5 text-sm text-slate-800';
  const labelClass = 'block text-xs font-medium text-slate-600';

  return (
    <div className="min-h-0 flex-1 space-y-4 overflow-y-auto px-6 py-4">
          {!result ? (
            <>
              <p className="text-xs leading-relaxed text-slate-600">
                {CHALLENGE_COPY.intro}
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
                        {EVIDENCE_ROLE_COPY[role]}
                      </option>
                    ))}
                  </select>
                </label>
              ) : null}

              {challengeType === 'CORRECT_CAPABILITY_MAPPING' ? (
                <label className={labelClass}>
                  Record to move here
                  {movableLoading ? (
                    <div className="mt-1 h-9 skeleton rounded-lg" />
                  ) : movable.length === 0 ? (
                    <p className="mt-1 text-xs font-normal text-slate-500">
                      Every record in this system is already filed under this capability, so
                      there is nothing to move. A record can only be re-filed within one system.
                    </p>
                  ) : (
                    <select
                      value={evidenceId}
                      onChange={(event) => setEvidenceId(event.target.value)}
                      className={`mt-1 ${inputClass}`}
                    >
                      <option value="">Select…</option>
                      {movable.map(({ record, capabilityName }) => (
                        <option key={record.evidence_id} value={record.evidence_id}>
                          {record.source_reference}
                          {record.source_title ? ` — ${record.source_title}` : ''} (now under{' '}
                          {capabilityName})
                        </option>
                      ))}
                    </select>
                  )}
                </label>
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
                Submitting as {approverCopy('eng_manager_sarah')}. Previous and new assessments are both kept.
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
                    A new evidence record was created ({result.evidence_created}).
                  </span>
                ) : null}
                {result.evidence_moved ? (
                  <span className="mt-1 block text-xs text-slate-500">
                    An evidence record was moved ({result.evidence_moved}).
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

      {/* The actions sit at the end of the scroll flow rather than in a pinned
          footer, so the submit control and the error notice above it are always
          adjacent — a fixed footer put them a scroll apart. */}
      <div className="flex items-center justify-end gap-3 border-t border-slate-900/5 pt-4">
        <button
          type="button"
          onClick={onBack}
          className="motion-press rounded-xl px-4 py-2 text-sm font-medium text-slate-600 hover:bg-white/50"
        >
          {CHALLENGE_COPY.back}
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
      </div>
    </div>
  );
}
