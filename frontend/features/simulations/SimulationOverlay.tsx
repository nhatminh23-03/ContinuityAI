'use client';

import { type CSSProperties, useEffect, useMemo, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useMutation, useQuery } from '@tanstack/react-query';
import type { SimulationResponse, SimulationState } from '@/types/api';
import { api, queryKeys } from '@/lib/api/endpoints';
import { ApiError } from '@/lib/api/client';
import { RiskClassChip, RiskIndex } from '@/components/status';
import { SIM_BANNER, SIM_DISCLAIMER } from '@/lib/copy';
import { ImpactRow } from './ImpactRow';

/**
 * The counterfactual sandbox. Models unavailability — never departure — and
 * prescribes nothing. Higher is worse: 74 → 93 reads as deterioration.
 */

function StateBlock({ label, state }: { label: string; state: SimulationState }) {
  return (
    <div className="rounded-2xl bg-white/50 p-4">
      <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
        {label}
      </div>
      <div className="mt-2 flex items-center gap-3">
        <RiskIndex value={state.continuity_risk_index} />
        <RiskClassChip riskClass={state.continuity_risk_class} />
      </div>
      <div className="mt-3 text-xs text-slate-600 tabular-nums">
        {state.critical_gap_count} with no proven coverage · {state.degraded_capability_count} with
        no resilient backup · {state.covered_capability_count} covered
      </div>
    </div>
  );
}

export function SimulationOverlay({
  systemId,
  defaultEngineerId,
  selectedCapabilityId,
  onClose,
}: {
  systemId: string;
  defaultEngineerId?: string;
  selectedCapabilityId?: string;
  onClose: () => void;
}) {
  const router = useRouter();
  const panelRef = useRef<HTMLDivElement>(null);

  const graphQuery = useQuery({
    queryKey: queryKeys.systemGraph(systemId),
    queryFn: () => api.getSystemGraph(systemId),
  });
  const engineers = useMemo(
    () =>
      (graphQuery.data?.nodes ?? [])
        .filter((node) => node.type === 'ENGINEER')
        .map((node) => ({
          id: node.id,
          name: node.label,
          role: typeof node.metadata?.role === 'string' ? node.metadata.role : undefined,
        })),
    [graphQuery.data],
  );

  const [engineerId, setEngineerId] = useState<string | undefined>(defaultEngineerId);
  useEffect(() => {
    if (!engineerId && engineers.length > 0) {
      setEngineerId(defaultEngineerId ?? engineers[0].id);
    }
  }, [engineers, engineerId, defaultEngineerId]);

  const mutation = useMutation({
    mutationFn: (targetEngineerId: string) =>
      api.runSimulation({
        simulation_type: 'ENGINEER_UNAVAILABLE',
        engineer_id: targetEngineerId,
        scope: { type: 'SYSTEM', id: systemId },
      }),
  });
  const { mutate } = mutation;

  useEffect(() => {
    if (engineerId) mutate(engineerId);
  }, [engineerId, mutate]);

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

  const result: SimulationResponse | undefined = mutation.data;
  const engineerName = engineers.find((e) => e.id === engineerId)?.name ?? engineerId;
  const candidateCapabilityId =
    result?.capability_impacts.find((impact) => impact.after === 'CRITICAL_GAP')?.capability_id ??
    selectedCapabilityId ??
    result?.capability_impacts[0]?.capability_id;

  return (
    <div className="fixed inset-0 z-50" role="dialog" aria-modal="true" aria-label="Simulation sandbox">
      <button type="button" aria-label="Close" onClick={onClose} className="motion-fade absolute inset-0 bg-slate-900/40" />
      <div
        ref={panelRef}
        tabIndex={-1}
        className="glass-panel motion-modal absolute left-1/2 top-1/2 flex max-h-[90vh] w-[720px] max-w-[calc(100vw-32px)] -translate-x-1/2 -translate-y-1/2 flex-col rounded-3xl outline-none"
      >
        <header className="border-b border-slate-900/5 px-6 py-4">
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-lg font-medium text-slate-900">
              What if {engineerName ?? '…'} were unavailable?
            </h2>
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
          <p className="mt-1 text-xs font-medium text-slate-600">{SIM_BANNER}</p>
          <label className="mt-3 flex items-center gap-2 text-xs font-medium text-slate-600">
            Engineer
            <select
              value={engineerId ?? ''}
              onChange={(event) => setEngineerId(event.target.value)}
              className="rounded-lg border border-slate-900/10 bg-white/70 px-2 py-1.5 text-xs font-medium text-slate-800"
            >
              {engineers.map((engineer) => (
                <option key={engineer.id} value={engineer.id}>
                  {engineer.name}
                  {engineer.role ? ` — ${engineer.role}` : ''}
                </option>
              ))}
            </select>
          </label>
        </header>

        <div className="min-h-0 flex-1 overflow-y-auto px-6 py-4">
          {mutation.isPending || (!result && !mutation.isError) ? (
            <div className="space-y-4">
              <div className="text-sm text-slate-600">Running coverage simulation…</div>
              <div className="h-28 skeleton rounded-2xl" />
              <div className="h-40 skeleton rounded-2xl" />
            </div>
          ) : mutation.isError ? (
            <div className="text-sm text-slate-600">
              The simulation could not be run.
              <span className="mt-1 block text-xs text-slate-500">
                {mutation.error instanceof ApiError ? `Error code: ${mutation.error.code}` : ''}
              </span>
            </div>
          ) : result ? (
            <>
              {/* A wider beat than the list default: current, then arrow, then
                  simulated. The sequence is the causal claim the panel makes,
                  so it is worth reading as three steps rather than one. */}
              <div
                className="motion-stagger grid grid-cols-[1fr_auto_1fr] items-center gap-3"
                style={{ '--stagger': '110ms' } as CSSProperties}
              >
                <StateBlock label="Today" state={result.before} />
                <span aria-hidden className="text-2xl text-slate-400">
                  →
                </span>
                <StateBlock label="If unavailable" state={result.after} />
              </div>
              <div className="mt-2 text-center text-xs font-medium text-slate-600">
                {result.before.continuity_risk_class} → {result.after.continuity_risk_class}
              </div>

              {result.summary ? (
                <p className="mt-4 text-sm leading-relaxed text-slate-700">{result.summary}</p>
              ) : null}

              {result.capability_impacts.length > 0 ? (
                <ul className="motion-stagger mt-4 divide-y divide-slate-900/5">
                  {result.capability_impacts.map((impact) => (
                    <ImpactRow key={impact.capability_id} impact={impact} />
                  ))}
                </ul>
              ) : (
                <p className="mt-4 text-sm text-slate-600">
                  No coverage would be lost in this scenario.
                </p>
              )}

              <p className="mt-4 text-xs text-slate-500">{SIM_DISCLAIMER}</p>
            </>
          ) : null}
        </div>

        <footer className="flex items-center justify-end gap-3 border-t border-slate-900/5 px-6 py-4">
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl px-4 py-2 text-sm font-medium text-slate-600 hover:bg-white/50"
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={!result || !candidateCapabilityId}
            onClick={() =>
              result &&
              candidateCapabilityId &&
              router.push(
                `/systems/${systemId}/candidates?simulation=${result.simulation_id}&capability=${candidateCapabilityId}`,
              )
            }
            className="motion-press rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
          >
            Find backup candidates
          </button>
        </footer>
      </div>
    </div>
  );
}
