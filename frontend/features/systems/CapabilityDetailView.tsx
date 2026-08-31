'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { api, queryKeys } from '@/lib/api/endpoints';
import { ApiError } from '@/lib/api/client';
import {
  ConfidenceLabel,
  ExposurePill,
  MetricLabel,
  RiskClassChip,
  RiskIndex,
} from '@/components/status';
import { ACTION_COPY, CRITICALITY_COPY, HINT_COPY } from '@/lib/copy';
import { EngineerBadge } from '@/components/people';
import { InfoHint } from '@/components/InfoHint';
import { CoverageCard } from './CoverageCard';
import { WhyPanel } from './WhyPanel';
import { EvidenceDrawer } from '@/features/evidence/EvidenceDrawer';

/**
 * Engineer-by-engineer readiness for one capability. INSUFFICIENT_EVIDENCE
 * is a designed state: a null index renders as an em dash inside the dashed
 * treatment, never as a manufactured number.
 */
export function CapabilityDetailView({ capabilityId }: { capabilityId: string }) {
  const [whyOpen, setWhyOpen] = useState(false);
  const [evidence, setEvidence] = useState<{ engineerId?: string; engineerName?: string } | null>(
    null,
  );

  const capabilityQuery = useQuery({
    queryKey: queryKeys.capability(capabilityId),
    queryFn: () => api.getCapability(capabilityId),
  });
  const systemId = capabilityQuery.data?.system_id;
  const systemQuery = useQuery({
    queryKey: queryKeys.system(systemId ?? ''),
    queryFn: () => api.getSystem(systemId ?? ''),
    enabled: Boolean(systemId),
  });
  const platformsQuery = useQuery({
    queryKey: queryKeys.platforms,
    queryFn: api.listPlatforms,
  });

  if (capabilityQuery.isPending) {
    return (
      <div className="mx-auto max-w-4xl space-y-6 py-6">
        <div className="frosted-card h-32 skeleton" />
        <div className="frosted-card h-60 skeleton" />
      </div>
    );
  }

  if (capabilityQuery.isError) {
    return (
      <div className="mx-auto max-w-4xl py-6">
        <div className="frosted-card p-6 text-sm text-slate-600">
          This capability could not be loaded.
          <span className="mt-1 block text-xs text-slate-500">
            {capabilityQuery.error instanceof ApiError
              ? `Error code: ${capabilityQuery.error.code}`
              : 'Unexpected error.'}
          </span>
          <Link href="/" className="mt-3 block text-xs font-medium text-slate-700 underline">
            Back to the dashboard
          </Link>
        </div>
      </div>
    );
  }

  const capability = capabilityQuery.data;
  const insufficient = capability.exposure === 'INSUFFICIENT_EVIDENCE';
  // Platform › System › Component › Capability. This is the only place in the
  // product where all four levels of the hierarchy appear on one line.
  const platformName = platformsQuery.data?.platforms.find(
    (platform) => platform.platform_id === systemQuery.data?.platform_id,
  )?.name;
  const componentName = systemQuery.data?.components.find(
    (component) => component.component_id === capability.component_id,
  )?.name;

  return (
    <div className="mx-auto max-w-4xl py-6">
      <nav aria-label="Breadcrumb" className="text-xs font-medium text-slate-500">
        <Link href="/" className="hover:text-slate-900 hover:underline">
          {platformName ?? 'Dashboard'}
        </Link>
        <span className="mx-1.5">›</span>
        <Link
          href={`/systems/${capability.system_id}`}
          className="hover:text-slate-900 hover:underline"
        >
          {systemQuery.data?.name ?? capability.system_id}
        </Link>
        {componentName ? (
          <>
            <span className="mx-1.5">›</span>
            <span>{componentName}</span>
          </>
        ) : null}
        <span className="mx-1.5">›</span>
        <span className="text-slate-700">{capability.name}</span>
      </nav>

      <div className="mt-2 flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <h1 className="text-3xl font-medium tracking-tight text-slate-900">{capability.name}</h1>
          <p className="mt-1 max-w-2xl text-[15px] text-slate-600">{capability.description}</p>
        </div>
        <Link
          href={`/systems/${capability.system_id}?capability=${capability.capability_id}&simulate=1`}
          className="motion-press rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-800"
        >
          {ACTION_COPY.simulate}
        </Link>
      </div>

      <div
        className={`mt-6 ${insufficient ? 'pill-insufficient rounded-[20px]' : 'frosted-card'} p-6`}
      >
        <div className="flex flex-wrap items-center gap-x-6 gap-y-3">
          <div>
            <MetricLabel hint={HINT_COPY.riskIndex}>Continuity risk</MetricLabel>
            <div className="mt-2 flex items-center gap-3">
              <RiskIndex value={capability.continuity_risk_index} />
              <RiskClassChip riskClass={capability.continuity_risk_class} />
            </div>
          </div>
          <div className="flex flex-col gap-2">
            <ExposurePill exposure={capability.exposure} />
            <ConfidenceLabel confidence={capability.evidence_confidence} hint />
            <span className="inline-flex items-center gap-1 text-xs text-slate-600">
              {CRITICALITY_COPY[capability.operational_criticality]} importance
              <InfoHint label="importance" text={HINT_COPY.criticality} />
            </span>
          </div>
          <button
            type="button"
            onClick={() => setWhyOpen(true)}
            className="ml-auto text-xs font-medium text-slate-600 underline decoration-slate-300 underline-offset-2 hover:text-slate-900"
          >
            How was this worked out?
          </button>
        </div>
        {insufficient ? (
          <p className="mt-4 text-sm text-slate-600">
            Not enough evidence for a responsible assessment. No index or class is assigned —
            gathering evidence is the next step, not guessing.
          </p>
        ) : null}
        <div className="mt-4 flex flex-wrap gap-8">
          {capability.primary_engineer ? (
            <div>
              <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                Strongest demonstrated coverage
              </div>
              <div className="mt-1.5">
                <EngineerBadge name={capability.primary_engineer.name} />
              </div>
            </div>
          ) : null}
          {capability.best_remaining_coverage ? (
            <div>
              <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                Best remaining
              </div>
              <div className="mt-1.5">
                <EngineerBadge name={capability.best_remaining_coverage.name} />
              </div>
            </div>
          ) : null}
        </div>
      </div>

      <div className="mt-6">
        <CoverageCard
          capabilityId={capabilityId}
          onViewEvidence={(engineerId, engineerName) =>
            setEvidence({ engineerId, engineerName })
          }
        />
      </div>
      <div className="mt-4">
        <button
          type="button"
          onClick={() => setEvidence({})}
          className="text-xs font-medium text-slate-600 underline decoration-slate-300 underline-offset-2 hover:text-slate-900"
        >
          View all evidence for this capability
        </button>
      </div>

      {whyOpen && systemQuery.data ? (
        <WhyPanel
          system={systemQuery.data}
          capabilityId={capabilityId}
          onClose={() => setWhyOpen(false)}
        />
      ) : null}

      {evidence ? (
        <EvidenceDrawer
          capabilityId={capabilityId}
          engineerId={evidence.engineerId}
          engineerName={evidence.engineerName}
          onClose={() => setEvidence(null)}
        />
      ) : null}
    </div>
  );
}
