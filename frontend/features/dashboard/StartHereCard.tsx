'use client';

import Link from 'next/link';
import { useQueries, useQuery } from '@tanstack/react-query';
import type { PlatformSummary } from '@/types/api';
import { api, queryKeys } from '@/lib/api/endpoints';
import { EngineerBadge, ReadinessLadder } from '@/components/people';
import { ExposurePill } from '@/components/status';
import { ACTION_COPY, CRITICALITY_COPY, ruleCopy } from '@/lib/copy';
import { sortSystemsByRisk } from './sort';
import { capabilitiesFromGraph, defaultCapabilityId } from '@/features/systems/capabilities';

/**
 * The one thing worth looking at first, named in words and with a person
 * attached.
 *
 * The dashboard reports totals — "4 capabilities depend on one person" — without
 * ever saying which capabilities or which person, so the product's actual
 * subject sat three clicks below its own home screen. This card names it and
 * links straight into the flow.
 *
 * Every value shown is received: the system is chosen by the server's risk
 * index, the capability by the server's coverage state, and the reasons are the
 * server's own rule codes rendered through the reviewed copy in lib/copy.ts.
 * Selecting which received row to show first is display ordering, the same work
 * `sortSystemsByRisk` and `defaultCapabilityId` already do elsewhere — nothing
 * here computes risk, readiness or coverage.
 */
export function StartHereCard({ platforms }: { platforms: PlatformSummary[] }) {
  // Identical query keys to SystemsTable, so this shares its cache rather than
  // issuing a second round of requests.
  const systemsResults = useQueries({
    queries: platforms.map((platform) => ({
      queryKey: queryKeys.platformSystems(platform.platform_id),
      queryFn: () => api.listPlatformSystems(platform.platform_id),
    })),
  });
  const systems = sortSystemsByRisk(systemsResults.flatMap((result) => result.data?.systems ?? []));
  const topSystem = systems[0];

  const graphQuery = useQuery({
    queryKey: queryKeys.systemGraph(topSystem?.system_id ?? ''),
    queryFn: () => api.getSystemGraph(topSystem!.system_id),
    enabled: Boolean(topSystem),
  });

  const capabilityId = graphQuery.data
    ? defaultCapabilityId(capabilitiesFromGraph(graphQuery.data))
    : undefined;

  const capabilityQuery = useQuery({
    queryKey: queryKeys.capability(capabilityId ?? ''),
    queryFn: () => api.getCapability(capabilityId!),
    enabled: Boolean(capabilityId),
  });

  const loading =
    systemsResults.some((result) => result.isPending) ||
    (Boolean(topSystem) && graphQuery.isPending) ||
    (Boolean(capabilityId) && capabilityQuery.isPending);

  if (loading) return <div className="frosted-card mt-6 h-44 skeleton" />;

  const capability = capabilityQuery.data;
  // The dashboard must not break because its lead story could not be assembled;
  // the platform cards and the systems table below stand on their own.
  if (!topSystem || !capability) return null;

  const primary = capability.primary_engineer;
  // Criticality is stated in the subtitle, so repeating it in the reason list
  // would spend a line saying the same thing twice.
  const reasons = (capability.rules_triggered ?? [])
    .filter((code) => code !== 'CRITICAL_CAPABILITY' && code !== 'HIGH_CAPABILITY')
    .slice(0, 3);

  const href =
    `/systems/${topSystem.system_id}?capability=${capability.capability_id}&simulate=1`;

  return (
    <section className="frosted-card motion-rise mt-6 p-6">
      <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Start here</div>

      <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-2">
        <h2 className="text-2xl font-medium tracking-tight text-slate-900">{capability.name}</h2>
        <ExposurePill exposure={capability.exposure} />
      </div>
      <p className="mt-1 text-sm text-slate-600">
        {topSystem.name} · {CRITICALITY_COPY[capability.operational_criticality]} importance
      </p>

      {primary ? (
        <div className="mt-5 flex flex-wrap items-center justify-between gap-x-6 gap-y-3 rounded-2xl bg-slate-900/[0.035] p-4 shadow-[inset_0_0_0_1px_rgba(27,27,29,0.06)]">
          <span className="flex flex-col gap-1">
            <span className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
              Strongest demonstrated coverage
            </span>
            <EngineerBadge name={primary.name} />
          </span>
          <ReadinessLadder level={primary.readiness} />
        </div>
      ) : null}

      {reasons.length > 0 ? (
        <ul className="motion-stagger mt-4 space-y-1.5">
          {reasons.map((code) => (
            <li key={code} className="flex items-start gap-2 text-sm text-slate-700">
              <span aria-hidden className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-slate-400" />
              {ruleCopy(code)}
            </li>
          ))}
        </ul>
      ) : null}

      <Link
        href={href}
        className="motion-press mt-5 inline-flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-800"
      >
        {primary ? ACTION_COPY.simulateFor(primary.name) : ACTION_COPY.simulate}
        <span aria-hidden>→</span>
      </Link>
    </section>
  );
}
