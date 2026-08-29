'use client';

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { api, queryKeys } from '@/lib/api/endpoints';
import { PlatformCard } from '@/features/dashboard/PlatformCard';
import { SystemsTable } from '@/features/dashboard/SystemsTable';
import { FirstRunStrip } from '@/features/dashboard/FirstRunStrip';
import { StartHereCard } from '@/features/dashboard/StartHereCard';
import { ApiError } from '@/lib/api/client';

export default function DashboardPage() {
  const queryClient = useQueryClient();
  const platformsQuery = useQuery({
    queryKey: queryKeys.platforms,
    queryFn: api.listPlatforms,
  });

  return (
    <div className="mx-auto max-w-5xl py-6">
      <h1 className="text-4xl font-medium tracking-tight text-slate-900">Knowledge Resilience</h1>
      <p className="mt-2 text-[15px] text-slate-600">
        Which critical work depends on one person — and what happens if they step away?
      </p>

      {platformsQuery.isPending ? (
        <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-2">
          <div className="frosted-card h-48 skeleton" />
          <div className="frosted-card h-48 skeleton" />
        </div>
      ) : platformsQuery.isError ? (
        <div className="frosted-card mt-8 p-6">
          <div className="text-sm font-medium text-slate-900">
            The platform overview could not be loaded.
          </div>
          <div className="mt-1 text-xs text-slate-500">
            {platformsQuery.error instanceof ApiError
              ? `Error code: ${platformsQuery.error.code}`
              : 'Unexpected error.'}
          </div>
          <button
            type="button"
            onClick={() => queryClient.invalidateQueries({ queryKey: queryKeys.platforms })}
            className="mt-4 rounded-lg bg-white/70 px-3 py-1.5 text-xs font-medium text-slate-700 ring-1 ring-white/60 hover:bg-white"
          >
            Try again
          </button>
        </div>
      ) : (
        <>
          {/* What to do, then the one thing worth doing first, then the totals.
              The scoreboard is still here — it just no longer opens the page. */}
          <FirstRunStrip />
          <StartHereCard platforms={platformsQuery.data.platforms} />
          <section className="mt-8">
            <h2 className="text-lg font-medium text-slate-900">Platforms</h2>
            <p className="mt-1 text-xs text-slate-600">
              Each platform groups the systems listed below —{' '}
              {platformsQuery.data.platforms.length} platforms,{' '}
              {platformsQuery.data.platforms.reduce((total, p) => total + p.system_count, 0)}{' '}
              systems in all.
            </p>
            <div className="motion-stagger mt-4 grid grid-cols-1 gap-6 md:grid-cols-2">
              {platformsQuery.data.platforms.map((platform) => (
                <PlatformCard key={platform.platform_id} platform={platform} />
              ))}
            </div>
          </section>
          <SystemsTable platforms={platformsQuery.data.platforms} />
        </>
      )}
    </div>
  );
}
