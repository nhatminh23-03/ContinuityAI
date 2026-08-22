'use client';

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { api, queryKeys } from '@/lib/api/endpoints';
import { SystemsTable } from '@/features/dashboard/SystemsTable';
import { ApiError } from '@/lib/api/client';

/**
 * The sidebar's Systems destination: every system across every platform,
 * ordered by risk. The dashboard answers "how are we doing?" with platform
 * cards on top; this page answers "which system do I open?" and nothing else.
 */
export default function SystemsPage() {
  const queryClient = useQueryClient();
  const platformsQuery = useQuery({
    queryKey: queryKeys.platforms,
    queryFn: api.listPlatforms,
  });

  return (
    <div className="mx-auto max-w-5xl py-6">
      <h1 className="text-4xl font-medium tracking-tight text-slate-900">Systems</h1>
      <p className="mt-2 text-[15px] text-slate-600">
        Every system across all platforms, highest continuity risk first.
      </p>

      {platformsQuery.isPending ? (
        <div className="frosted-card mt-8 space-y-3 p-6">
          {[0, 1, 2].map((row) => (
            <div key={row} className="h-12 skeleton rounded-xl" />
          ))}
        </div>
      ) : platformsQuery.isError ? (
        <div className="frosted-card mt-8 p-6">
          <div className="text-sm font-medium text-slate-900">
            The systems list could not be loaded.
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
        <SystemsTable platforms={platformsQuery.data.platforms} />
      )}
    </div>
  );
}
