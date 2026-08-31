/**
 * Status primitives for capabilities and systems — the only place saturated
 * colour appears in the interface. People never receive these treatments.
 */

import type {
  CapabilityExposure,
  ContinuityRiskClass,
  EvidenceConfidence,
  KnowledgeDriftStatus,
} from '@/types/api';
import {
  CONFIDENCE_COPY,
  DRIFT_COPY,
  EXPOSURE_COPY,
  HINT_COPY,
  SYSTEM_EXPOSURE_COPY,
} from '@/lib/copy';
import { InfoHint } from '@/components/InfoHint';

const EXPOSURE_CLASS: Record<CapabilityExposure, string> = {
  COVERED: 'glass-chip chip-low text-[color:var(--status-covered)]',
  DEGRADED: 'glass-chip chip-high text-[color:var(--status-degraded)]',
  CRITICAL_GAP: 'glass-chip chip-critical text-[color:var(--status-critical-gap)]',
  INSUFFICIENT_EVIDENCE: 'pill-insufficient text-[color:var(--status-insufficient)]',
};

export function ExposurePill({
  exposure,
  scope = 'capability',
}: {
  exposure: CapabilityExposure;
  /** A system carries the worst of its capabilities' states, not its own. */
  scope?: 'capability' | 'system';
}) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold whitespace-nowrap ${EXPOSURE_CLASS[exposure]}`}
    >
      {scope === 'system' ? SYSTEM_EXPOSURE_COPY[exposure] : EXPOSURE_COPY[exposure]}
    </span>
  );
}

const CLASS_CHIP: Record<ContinuityRiskClass, string> = {
  LOW: 'chip-low text-[color:var(--status-covered)]',
  MODERATE: 'chip-moderate text-[color:var(--status-degraded)]',
  HIGH: 'chip-high text-[color:var(--status-degraded)]',
  CRITICAL: 'chip-critical text-[color:var(--status-critical-gap)]',
};

export function RiskClassChip({ riskClass }: { riskClass: ContinuityRiskClass | null }) {
  if (riskClass === null) {
    return (
      <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold text-slate-400">
        —
      </span>
    );
  }
  return (
    <span
      className={`glass-chip inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${CLASS_CHIP[riskClass]}`}
    >
      {riskClass}
    </span>
  );
}

/**
 * Large light-weight tabular numeral. Null renders as an em dash, never 0.
 *
 * The headline size carries "/100" because a bare 74 reads as a percentage or a
 * probability, which is exactly what the index is not. The compact size appears
 * in lists beside other numbers where the scale is already established, and
 * `showScale` turns the suffix off where it would only add noise.
 */
export function RiskIndex({
  value,
  size = 'lg',
  showScale,
}: {
  value: number | null;
  size?: 'lg' | 'md';
  showScale?: boolean;
}) {
  const sizeClass = size === 'lg' ? 'text-5xl' : 'text-2xl';
  const withScale = showScale ?? size === 'lg';
  return (
    <span className={`${sizeClass} font-light tabular-nums leading-none text-slate-900`}>
      {value ?? '—'}
      {value !== null && withScale ? (
        <span className="ml-0.5 text-[0.4em] font-medium text-slate-500"> / 100</span>
      ) : null}
    </span>
  );
}

/** The headline term plus its explanation, for the first place each appears. */
export function MetricLabel({ children, hint }: { children: string; hint?: string }) {
  return (
    <span className="inline-flex items-center gap-1 text-xs font-semibold uppercase tracking-wide text-slate-500">
      {children}
      {hint ? <InfoHint label={children} text={hint} /> : null}
    </span>
  );
}

export function DriftLabel({ status }: { status: KnowledgeDriftStatus }) {
  return <span className="text-xs font-medium text-slate-600">{DRIFT_COPY[status]}</span>;
}

export function ConfidenceLabel({
  confidence,
  /**
   * Off by default. This label renders inside the dashboard's row link, and a
   * button nested in an anchor is invalid — clicking the hint navigated to the
   * system instead of explaining the term. Opt in only where the label is not
   * inside another interactive element.
   */
  hint = false,
}: {
  confidence: EvidenceConfidence;
  hint?: boolean;
}) {
  return (
    <span className="inline-flex items-center gap-1 text-xs font-medium text-slate-600">
      Evidence:{' '}
      <span className="font-semibold text-slate-700">{CONFIDENCE_COPY[confidence]}</span>
      {hint ? <InfoHint label="evidence confidence" text={HINT_COPY.evidenceConfidence} /> : null}
    </span>
  );
}
