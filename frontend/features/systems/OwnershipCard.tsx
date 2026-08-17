import type { DeclaredOwnership } from '@/types/api';
import { EngineerBadge } from '@/components/people';

/**
 * Declared ownership is not demonstrated coverage — the mismatch note is the
 * product's core demonstration and must stay visible.
 */
export function OwnershipCard({ ownership }: { ownership: DeclaredOwnership | null | undefined }) {
  return (
    <div className="frosted-card p-6">
      <h2 className="text-sm font-semibold text-slate-900">Declared ownership</h2>
      {ownership ? (
        <div className="mt-4 space-y-3">
          <EngineerBadge name={ownership.name} role={`Source: ${ownership.source}`} />
          {ownership.mismatch_detected ? (
            <p className="rounded-xl bg-[color:var(--status-degraded)]/10 px-3 py-2 text-xs font-medium text-[color:var(--status-degraded)]">
              Differs from demonstrated coverage
            </p>
          ) : null}
        </div>
      ) : (
        <p className="mt-4 text-sm text-slate-500">No declared owner recorded.</p>
      )}
    </div>
  );
}
