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
import { DRIFT_COPY } from '@/lib/copy';

const EXPOSURE_LABEL: Record<CapabilityExposure, string> = {
  COVERED: 'Covered',
  DEGRADED: 'Degraded',
  CRITICAL_GAP: 'Critical gap',
  INSUFFICIENT_EVIDENCE: 'Insufficient evidence',
};

const EXPOSURE_CLASS: Record<CapabilityExposure, string> = {
  COVERED: 'glass-chip chip-low text-[color:var(--status-covered)]',
  DEGRADED: 'glass-chip chip-high text-[color:var(--status-degraded)]',
  CRITICAL_GAP: 'glass-chip chip-critical text-[color:var(--status-critical-gap)]',
  INSUFFICIENT_EVIDENCE: 'pill-insufficient text-[color:var(--status-insufficient)]',
};

export function ExposurePill({ exposure }: { exposure: CapabilityExposure }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold whitespace-nowrap ${EXPOSURE_CLASS[exposure]}`}
    >
      {EXPOSURE_LABEL[exposure]}
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

/** Large light-weight tabular numeral. Null renders as an em dash, never 0. */
export function RiskIndex({ value, size = 'lg' }: { value: number | null; size?: 'lg' | 'md' }) {
  const sizeClass = size === 'lg' ? 'text-5xl' : 'text-2xl';
  return (
    <span className={`${sizeClass} font-light tabular-nums leading-none text-slate-900`}>
      {value ?? '—'}
    </span>
  );
}

export function DriftLabel({ status }: { status: KnowledgeDriftStatus }) {
  return <span className="text-xs font-medium text-slate-600">{DRIFT_COPY[status]}</span>;
}

export function ConfidenceLabel({ confidence }: { confidence: EvidenceConfidence }) {
  return (
    <span className="text-xs font-medium text-slate-600">
      Confidence: <span className="font-semibold text-slate-700">{confidence}</span>
    </span>
  );
}
