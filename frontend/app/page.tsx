'use client';

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { api, queryKeys } from '@/lib/api/endpoints';
import { PlatformCard } from '@/features/dashboard/PlatformCard';
import { SystemsTable } from '@/features/dashboard/SystemsTable';
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
        Where does critical capability depend on one person?
      </p>

      {platformsQuery.isPending ? (
        <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-2">
          <div className="frosted-card h-48 animate-pulse" />
          <div className="frosted-card h-48 animate-pulse" />
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
          <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-2">
            {platformsQuery.data.platforms.map((platform) => (
              <PlatformCard key={platform.platform_id} platform={platform} />
            ))}
          </div>
          <SystemsTable platforms={platformsQuery.data.platforms} />
        </>
      )}
    </div>
  );
}
