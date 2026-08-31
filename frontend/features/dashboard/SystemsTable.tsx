'use client';

import Link from 'next/link';
import { useQueries } from '@tanstack/react-query';
import type { PlatformSummary, SystemSummary } from '@/types/api';
import { api, queryKeys } from '@/lib/api/endpoints';
import { ConfidenceLabel, DriftLabel, ExposurePill, RiskClassChip, RiskIndex } from '@/components/status';
import { sortSystemsByRisk } from './sort';
import { ACTION_COPY, CRITICALITY_COPY } from '@/lib/copy';

/**
 * All systems across every platform, sorted by risk descending — the
 * manager's "where do I look first?" list. Values are rendered as received.
 */
export function SystemsTable({ platforms }: { platforms: PlatformSummary[] }) {
  const results = useQueries({
    queries: platforms.map((platform) => ({
      queryKey: queryKeys.platformSystems(platform.platform_id),
      queryFn: () => api.listPlatformSystems(platform.platform_id),
    })),
  });

  if (results.some((result) => result.isPending)) {
    return (
      <div className="frosted-card mt-6 space-y-3 p-6">
        {[0, 1, 2].map((row) => (
          <div key={row} className="h-12 skeleton rounded-xl" />
        ))}
      </div>
    );
  }

  const platformNames = new Map(platforms.map((p) => [p.platform_id, p.name]));
  const systems: SystemSummary[] = sortSystemsByRisk(
    results.flatMap((result) => result.data?.systems ?? []),
  );
  const failedCount = results.filter((result) => result.isError).length;

  return (
    <div className="frosted-card mt-6 p-6">
      <h2 className="text-lg font-medium text-slate-900">Systems, most at risk first</h2>
      {failedCount > 0 ? (
        <p className="mt-2 text-xs text-slate-600">
          {failedCount === results.length
            ? 'The systems list could not be loaded.'
            : 'Some systems could not be loaded; showing the rest.'}
        </p>
      ) : null}
      <ul className="motion-stagger mt-4 divide-y divide-slate-900/5">
        {systems.map((system) => (
          <li key={system.system_id}>
            <div className="motion-press -mx-2 flex items-center gap-4 rounded-xl px-2 py-4 hover:bg-white/50">
              <Link
                href={`/systems/${system.system_id}`}
                className="group flex min-w-0 flex-1 items-center gap-4"
              >
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-medium text-slate-900 group-hover:underline">
                    {system.name}
                  </div>
                  <div className="text-xs text-slate-500">
                    {platformNames.get(system.platform_id) ?? system.platform_id} ·{' '}
                    {CRITICALITY_COPY[system.business_criticality]} importance
                  </div>
                </div>
                <ExposurePill exposure={system.exposure} scope="system" />
                <div className="hidden w-32 shrink-0 flex-col gap-0.5 lg:flex">
                  <ConfidenceLabel confidence={system.evidence_confidence} />
                  <DriftLabel status={system.drift_status} />
                </div>
                <div className="flex w-28 shrink-0 items-center justify-end gap-2">
                  <RiskIndex value={system.continuity_risk_index} size="md" />
                  <RiskClassChip riskClass={system.continuity_risk_class} />
                </div>
              </Link>
              <Link
                href={`/systems/${system.system_id}?simulate=1`}
                className="shrink-0 rounded-lg px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:bg-white/50 hover:text-slate-900"
              >
                {ACTION_COPY.simulateShort}
              </Link>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
