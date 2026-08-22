'use client';

import { useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import type { SystemDetail } from '@/types/api';
import { api, queryKeys } from '@/lib/api/endpoints';
import { RiskClassChip, RiskIndex } from '@/components/status';
import { CLASS_ANCHOR, modifierCopy, ruleCopy } from '@/lib/copy';

/**
 * The fired-rules list behind the risk index, plus the index arithmetic.
 * Every number shown is the server's own — the anchor comes from the class
 * it sent, the deltas from index_modifiers, the total from the index field.
 * Nothing is recomputed here.
 */
export function WhyPanel({
  system,
  capabilityId,
  onClose,
}: {
  system: SystemDetail;
  capabilityId?: string;
  onClose: () => void;
}) {
  const panelRef = useRef<HTMLDivElement>(null);
  const capabilityQuery = useQuery({
    queryKey: queryKeys.capability(capabilityId ?? ''),
    queryFn: () => api.getCapability(capabilityId ?? ''),
    enabled: Boolean(capabilityId),
  });

  useEffect(() => {
    const previouslyFocused = document.activeElement as HTMLElement | null;
    panelRef.current?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => {
      window.removeEventListener('keydown', onKey);
      previouslyFocused?.focus?.();
    };
  }, [onClose]);

  const capability = capabilityQuery.data;
  const anchor =
    capability?.continuity_risk_class != null
      ? CLASS_ANCHOR[capability.continuity_risk_class]
      : undefined;
  const showArithmetic =
    capability != null &&
    anchor !== undefined &&
    capability.continuity_risk_index !== null &&
    (capability.index_modifiers?.length ?? 0) > 0;

  return (
    <div className="fixed inset-0 z-50" role="dialog" aria-modal="true" aria-label="Why this risk?">
      <button
        type="button"
        aria-label="Close"
        onClick={onClose}
        className="motion-fade absolute inset-0 bg-slate-900/40"
      />
      <div
        ref={panelRef}
        tabIndex={-1}
        className="glass-panel motion-modal absolute left-1/2 top-1/2 max-h-[85vh] w-[560px] max-w-[calc(100vw-32px)] -translate-x-1/2 -translate-y-1/2 overflow-y-auto rounded-3xl p-6 outline-none"
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-medium text-slate-900">Why this risk?</h2>
            <div className="mt-1 flex items-center gap-2 text-sm text-slate-600">
              {system.name}
              <RiskIndex value={system.continuity_risk_index} size="md" />
              <RiskClassChip riskClass={system.continuity_risk_class} />
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="flex h-8 w-8 items-center justify-center rounded-full text-slate-500 hover:bg-white/60 hover:text-slate-900"
          >
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-4 w-4" aria-hidden>
              <path d="m4 4 8 8m0-8-8 8" strokeLinecap="round" />
            </svg>
          </button>
        </div>

        {system.rules_triggered?.length ? (
          <div className="mt-4">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              System rules that fired
            </h3>
            <ul className="motion-stagger mt-2 space-y-1.5">
              {system.rules_triggered.map((code) => (
                <li key={code} className="flex items-start gap-2 text-sm text-slate-700">
                  <span aria-hidden className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-slate-400" />
                  {ruleCopy(code)}
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {capability ? (
          <div className="mt-5 rounded-2xl bg-white/50 p-4">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="text-sm font-semibold text-slate-900">{capability.name}</h3>
              <RiskIndex value={capability.continuity_risk_index} size="md" />
              <RiskClassChip riskClass={capability.continuity_risk_class} />
            </div>
            {capability.rules_triggered?.length ? (
              <ul className="motion-stagger mt-3 space-y-1.5">
                {capability.rules_triggered.map((code) => (
                  <li key={code} className="flex items-start gap-2 text-sm text-slate-700">
                    <span aria-hidden className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-slate-400" />
                    {ruleCopy(code)}
                  </li>
                ))}
              </ul>
            ) : null}

            {showArithmetic ? (
              <div className="mt-4 border-t border-slate-900/5 pt-3">
                <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  How the index is reached
                </h4>
                <dl className="mt-2 space-y-1 text-sm tabular-nums">
                  <div className="flex justify-between gap-3 text-slate-700">
                    <dt>{capability.continuity_risk_class} anchor</dt>
                    <dd className="font-medium">{anchor}</dd>
                  </div>
                  {capability.index_modifiers?.map((modifier) => (
                    <div key={modifier.code} className="flex justify-between gap-3 text-slate-600">
                      <dt>{modifierCopy(modifier.code)}</dt>
                      <dd className="font-medium">
                        {modifier.delta >= 0 ? `+${modifier.delta}` : modifier.delta}
                      </dd>
                    </div>
                  ))}
                  <div className="flex justify-between gap-3 border-t border-slate-900/10 pt-1.5 font-semibold text-slate-900">
                    <dt>Continuity Risk Index</dt>
                    <dd>{capability.continuity_risk_index} / 100</dd>
                  </div>
                </dl>
              </div>
            ) : null}
          </div>
        ) : capabilityId && capabilityQuery.isError ? (
          <p className="mt-5 text-sm text-slate-600">
            The capability breakdown could not be loaded.
          </p>
        ) : capabilityId ? (
          <div className="mt-5 h-24 skeleton rounded-2xl" />
        ) : null}

        <p className="mt-4 text-xs text-slate-500">
          The index is a comparison number, not a probability.
        </p>
      </div>
    </div>
  );
}
