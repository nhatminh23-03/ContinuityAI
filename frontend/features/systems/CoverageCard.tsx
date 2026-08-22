'use client';

import { useQuery } from '@tanstack/react-query';
import { api, queryKeys } from '@/lib/api/endpoints';
import { ApiError } from '@/lib/api/client';
import { EngineerBadge } from '@/components/people';
import { ReadinessLadder } from '@/components/people';
import { ConfidenceLabel } from '@/components/status';

/**
 * Engineer coverage for the selected capability: monochrome ladders, no
 * numbers, no ranking — rows render in payload order.
 */
export function CoverageCard({
  capabilityId,
  onViewEvidence,
}: {
  capabilityId: string;
  onViewEvidence?: (engineerId: string, engineerName: string) => void;
}) {
  const query = useQuery({
    queryKey: queryKeys.capability(capabilityId),
    queryFn: () => api.getCapability(capabilityId),
  });

  return (
    <div className="frosted-card p-6">
      <div className="flex items-baseline justify-between gap-3">
        <h2 className="text-sm font-semibold text-slate-900">Coverage</h2>
        {query.data ? (
          <span className="truncate text-xs text-slate-500">{query.data.name}</span>
        ) : null}
      </div>
      {query.isPending ? (
        <div className="mt-4 space-y-3">
          {[0, 1, 2].map((row) => (
            <div key={row} className="h-10 skeleton rounded-xl" />
          ))}
        </div>
      ) : query.isError ? (
        <p className="mt-4 text-sm text-slate-500">
          Coverage could not be loaded.
          {query.error instanceof ApiError ? (
            <span className="ml-1 text-xs">Error code: {query.error.code}</span>
          ) : null}
        </p>
      ) : (
        <ul className="motion-stagger mt-4 space-y-4">
          {query.data.engineer_coverage.map((coverage) => (
            <li
              key={coverage.engineer_id}
              className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2"
            >
              <EngineerBadge name={coverage.name} />
              <span className="flex items-center gap-4">
                <ReadinessLadder level={coverage.readiness} />
                <span className="flex flex-col items-end leading-tight">
                  <span className="text-xs font-medium text-slate-600">{coverage.freshness}</span>
                  <span className="text-[11px] text-slate-500">
                    {coverage.last_demonstrated_at
                      ? `Last demonstrated ${coverage.last_demonstrated_at}`
                      : 'No dated evidence'}
                  </span>
                </span>
                <ConfidenceLabel confidence={coverage.evidence_confidence} />
                {onViewEvidence ? (
                  <button
                    type="button"
                    onClick={() => onViewEvidence(coverage.engineer_id, coverage.name)}
                    className="rounded-lg px-2 py-1 text-[11px] font-medium text-slate-500 hover:bg-white/60 hover:text-slate-900"
                  >
                    View evidence
                  </button>
                ) : null}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
