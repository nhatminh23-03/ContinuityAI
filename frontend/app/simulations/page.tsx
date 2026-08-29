'use client';

import { useState } from 'react';
import { useQueries, useQuery } from '@tanstack/react-query';
import { api, queryKeys } from '@/lib/api/endpoints';
import { SimulationOverlay } from '@/features/simulations/SimulationOverlay';

/**
 * Sandbox launcher: pick a system, open the unavailability sandbox.
 * Only SYSTEM scope exists in the MVP — platform scope is never offered.
 */
export default function SimulationsPage() {
  const [systemId, setSystemId] = useState<string>('');
  const [open, setOpen] = useState(false);

  const platformsQuery = useQuery({ queryKey: queryKeys.platforms, queryFn: api.listPlatforms });
  const systemsResults = useQueries({
    queries: (platformsQuery.data?.platforms ?? []).map((platform) => ({
      queryKey: queryKeys.platformSystems(platform.platform_id),
      queryFn: () => api.listPlatformSystems(platform.platform_id),
    })),
  });
  const systems = systemsResults.flatMap((result) => result.data?.systems ?? []);
  const loading =
    platformsQuery.isPending || systemsResults.some((result) => result.isPending);
  const selected = systemId || systems[0]?.system_id || '';

  return (
    <div className="mx-auto max-w-3xl py-6">
      <h1 className="text-4xl font-medium tracking-tight text-slate-900">Simulations</h1>
      <p className="mt-2 text-[15px] text-slate-600">
        Pick a system, then see which capabilities would lose proven coverage if one engineer
        were unavailable. Nothing changes in your real data.
      </p>

      <div className="frosted-card mt-8 p-6">
        <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
          System
          <select
            value={selected}
            onChange={(event) => setSystemId(event.target.value)}
            className="mt-2 block w-full rounded-xl border border-slate-900/10 bg-white/70 px-3 py-2.5 text-sm font-medium normal-case tracking-normal text-slate-800"
          >
            {systems.map((system) => (
              <option key={system.system_id} value={system.system_id}>
                {system.name}
              </option>
            ))}
          </select>
        </label>
        <button
          type="button"
          disabled={!selected || loading}
          onClick={() => setOpen(true)}
          className="motion-press mt-4 rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
        >
          {loading ? 'Loading systems…' : 'Open sandbox'}
        </button>
      </div>

      {open && selected ? (
        <SimulationOverlay systemId={selected} onClose={() => setOpen(false)} />
      ) : null}
    </div>
  );
}
