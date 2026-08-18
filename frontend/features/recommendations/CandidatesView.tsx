'use client';

import { useMemo, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { api, queryKeys } from '@/lib/api/endpoints';
import { ApiError } from '@/lib/api/client';
import { EvidenceDrawer } from '@/features/evidence/EvidenceDrawer';
import { CandidateCard } from './CandidateCard';
import { NotConsideredPanel } from './NotConsideredPanel';

export function CandidatesView({
  systemId,
  capabilityId,
  simulationId,
}: {
  systemId: string;
  capabilityId: string;
  simulationId?: string;
}) {
  const router = useRouter();
  const [evidenceEngineer, setEvidenceEngineer] = useState<{ id: string; name: string } | null>(
    null,
  );
  const [freeChoice, setFreeChoice] = useState('');

  const candidatesQuery = useQuery({
    queryKey: ['backup-candidates', capabilityId, simulationId],
    queryFn: () =>
      api.compareBackupCandidates({
        simulation_id: simulationId,
        capability_id: capabilityId,
        limit: 3,
      }),
  });
  const capabilityQuery = useQuery({
    queryKey: queryKeys.capability(capabilityId),
    queryFn: () => api.getCapability(capabilityId),
  });
  const systemQuery = useQuery({
    queryKey: queryKeys.system(systemId),
    queryFn: () => api.getSystem(systemId),
  });
  const graphQuery = useQuery({
    queryKey: queryKeys.systemGraph(systemId),
    queryFn: () => api.getSystemGraph(systemId),
  });

  const roles = useMemo(() => {
    const map = new Map<string, string>();
    for (const node of graphQuery.data?.nodes ?? []) {
      if (node.type === 'ENGINEER' && typeof node.metadata?.role === 'string') {
        map.set(node.id, node.metadata.role);
      }
    }
    return map;
  }, [graphQuery.data]);

  const primaryEngineerId = capabilityQuery.data?.primary_engineer?.engineer_id;

  const goToPlan = (backupEngineerId: string) => {
    const params = new URLSearchParams({ capability: capabilityId, backup: backupEngineerId });
    if (simulationId) params.set('simulation', simulationId);
    if (primaryEngineerId) params.set('primary', primaryEngineerId);
    router.push(`/plans/new?${params.toString()}`);
  };

  const otherEngineers = (graphQuery.data?.nodes ?? [])
    .filter(
      (node) =>
        node.type === 'ENGINEER' &&
        !candidatesQuery.data?.candidates.some((c) => c.engineer_id === node.id),
    )
    .map((node) => ({ id: node.id, name: node.label }));

  return (
    <div className="mx-auto max-w-5xl py-6">
      <nav aria-label="Breadcrumb" className="text-xs font-medium text-slate-500">
        <Link href={`/systems/${systemId}`} className="hover:text-slate-900 hover:underline">
          {systemQuery.data?.name ?? systemId}
        </Link>
        <span className="mx-1.5">›</span>
        <span className="text-slate-700">
          {capabilityQuery.data?.name ?? capabilityId}
        </span>
      </nav>
      <h1 className="mt-2 text-3xl font-medium tracking-tight text-slate-900">
        Backup candidates for {capabilityQuery.data?.name ?? '…'}
      </h1>
      <p className="mt-1 max-w-2xl text-[15px] text-slate-600">
        Technical candidates from demonstrated capability overlap. The manager chooses.
      </p>

      {candidatesQuery.isPending ? (
        <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-2">
          <div className="frosted-card h-72 animate-pulse" />
          <div className="frosted-card h-72 animate-pulse" />
        </div>
      ) : candidatesQuery.isError ? (
        <div className="frosted-card mt-8 p-6 text-sm text-slate-600">
          Candidates could not be compared.
          <span className="mt-1 block text-xs text-slate-500">
            {candidatesQuery.error instanceof ApiError
              ? `Error code: ${candidatesQuery.error.code}`
              : ''}
          </span>
        </div>
      ) : (
        <>
          {candidatesQuery.data.candidates.length === 0 ? (
            <div className="frosted-card mt-8 p-6 text-sm text-slate-600">
              {candidatesQuery.data.message ??
                'No technically adjacent candidates were found for this capability.'}
            </div>
          ) : (
            <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-2">
              {candidatesQuery.data.candidates.map((candidate) => (
                <CandidateCard
                  key={candidate.engineer_id}
                  candidate={candidate}
                  role={roles.get(candidate.engineer_id)}
                  onGeneratePlan={() => goToPlan(candidate.engineer_id)}
                  onViewEvidence={() =>
                    setEvidenceEngineer({ id: candidate.engineer_id, name: candidate.name })
                  }
                />
              ))}
            </div>
          )}

          {otherEngineers.length > 0 ? (
            <div className="mt-6 flex flex-wrap items-center gap-3 text-xs text-slate-600">
              <span>Or choose a different engineer:</span>
              <select
                value={freeChoice}
                onChange={(event) => setFreeChoice(event.target.value)}
                className="rounded-lg border border-slate-900/10 bg-white/70 px-2 py-1.5 text-xs font-medium text-slate-800"
              >
                <option value="">Select…</option>
                {otherEngineers.map((engineer) => (
                  <option key={engineer.id} value={engineer.id}>
                    {engineer.name}
                  </option>
                ))}
              </select>
              <button
                type="button"
                disabled={!freeChoice}
                onClick={() => goToPlan(freeChoice)}
                className="rounded-lg bg-white/70 px-3 py-1.5 font-medium text-slate-700 ring-1 ring-slate-900/10 hover:bg-white disabled:opacity-50"
              >
                Generate transfer plan
              </button>
            </div>
          ) : null}

          <div className="mt-8">
            <NotConsideredPanel disclaimer={candidatesQuery.data.disclaimer} />
          </div>
        </>
      )}

      {evidenceEngineer ? (
        <EvidenceDrawer
          capabilityId={capabilityId}
          engineerId={evidenceEngineer.id}
          engineerName={evidenceEngineer.name}
          onClose={() => setEvidenceEngineer(null)}
        />
      ) : null}
    </div>
  );
}
